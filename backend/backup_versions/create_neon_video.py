import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class NeonVideoGenerator:
    def __init__(self, image_path, output_path, duration=5.0, drawing_duration=None, fps=24):
        self.image_path = image_path
        self.output_path = output_path
        self.duration = duration
        self.drawing_duration = drawing_duration if drawing_duration is not None else duration
        self.fps = fps
        self.width = 1920
        self.height = 1080

    def _get_sorted_contours(self, img_bgr):
        # 2. Pre-process for NEON (Bright lines on Dark BG)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # For Neon, we want to detect BRIGHT things.
        # Simple threshold usually works best for "Glowing" items on black.
        # Everything brighter than 30/255 is considered "content".
        _, binary_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        
        # Clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
        
        # Use this mask as our "content" map
        self.blobs_binary = cleaned
        
        # Connected Components for sorting
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
        
        blobs = []
        for i in range(1, num_labels): # Skip 0 (black background)
            x, y, w, h, area = stats[i]
            if area > 10: 
                blobs.append({
                    'id': i, 'x': x, 'y': y, 'w': w, 'h': h, 'area': area,
                    'center_x': x + w/2
                })
        
        # Sort blobs: Big to Small (Structure first)
        blobs.sort(key=lambda b: (b['area'], -b['y']), reverse=True)
        
        return cleaned, blobs

    def generate(self):
        print(f"🎬 Processing Neon Video (Stroke Reveal) for: {self.image_path}")
        
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        # Load and prep image
        original_img = cv2.imread(self.image_path)
        if original_img is None:
            raise ValueError(f"Could not load image: {self.image_path}")
            
        h, w = original_img.shape[:2]
        scale = min(self.width/w, self.height/h)
        new_w, new_h = int(w * scale), int(h * scale)
        original_resized = cv2.resize(original_img, (new_w, new_h))
        
        y_offset = (self.height - new_h) // 2
        x_offset = (self.width - new_w) // 2
        
        # Get content map
        ink_map, blobs_meta = self._get_sorted_contours(original_resized)
        
        raw_contours, _ = cv2.findContours(ink_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        contour_structs = []
        for cnt in raw_contours:
            area = cv2.contourArea(cnt)
            if area > 10:
                contour_structs.append({'cnt': cnt, 'area': area})
        
        # Sort logic: PURE LEFT-TO-RIGHT (For sequential explanation flow)
        # We calculate the center-x of every contour and sort by that.
        
        all_contours = []
        for c in contour_structs:
            x, y, w, h = cv2.boundingRect(c['cnt'])
            c['center_x'] = x + w/2
            all_contours.append(c)
            
        # Sort strict Left-to-Right
        all_contours.sort(key=lambda c: c['center_x'])
        
        sorted_contours = [c['cnt'] for c in all_contours]
        
        # --- BACKGROUND CHANGE ---
        # BLACK Background (0)
        full_canvas_ref = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Create "Content Layer" (The colored neon parts)
        # Start with Black
        ink_display_color = np.zeros_like(original_resized)
        
        # Mask where content is (ink_map > 0)
        mask_bool = (ink_map > 0)
        
        # Copy original NEON pixels to those spots
        ink_display_color[mask_bool] = original_resized[mask_bool]
        
        # Place centered
        full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = ink_display_color
        
        total_perimeter = sum(cv2.arcLength(c, True) for c in sorted_contours)
        
        if total_perimeter == 0:
            print("⚠️ No contours. Static image.")
            clip = VideoClip(lambda t: full_canvas_ref, duration=self.duration)
            clip.write_videofile(self.output_path, fps=self.fps, codec='libx264')
            return

        target_draw_time = min(3.5, self.duration * 0.8)
        
        # --- NEW PACING LOGIC: OBJECT-BASED ---
        # User wants "boxes" (large) to create "faster".
        # We assign a "cost" to each contour.
        # Cost = Base_Cost (per object) + Length_Cost * Factor
        # High Base_Cost means purely "Sequential Item" pacing.
        # Low Base_Cost means "Pen Speed" pacing.
        # We want BIG items to be fast -> High Base Cost relative to length.
        
        contour_costs = []
        for cnt in sorted_contours:
            p_len = cv2.arcLength(cnt, True)
            # A moderate base cost ensures every item gets a "moment"
            # But length still matters a little so giant complex shapes take slightly longer than a dot.
            # Heuristic: 100px length ~= 1 generic "item tick"
            cost = 100 + p_len * 0.2 
            contour_costs.append(cost)
            
        total_cost = sum(contour_costs)
        
        print(f"   ⚡ Neon Stroke Logic: Completing in {target_draw_time:.2f}s (Object Pacing)")

        shifted_contours = []
        for cnt in sorted_contours:
            cnt_shift = cnt.copy()
            cnt_shift[:, 0, 0] += x_offset
            cnt_shift[:, 0, 1] += y_offset
            shifted_contours.append(cnt_shift)

        def make_frame(t):
            if target_draw_time <= 0: progress = 1.0
            else: progress = min(1.0, t / target_draw_time)
            
            current_target_cost = total_cost * progress
            
            # Start with Black Mask
            reveal_mask = np.zeros((self.height, self.width), dtype=np.uint8)
            
            accumulated_cost = 0
            
            for i, cnt in enumerate(shifted_contours):
                cost = contour_costs[i]
                p_len = cv2.arcLength(cnt, True)
                
                if accumulated_cost + cost <= current_target_cost:
                    # Fully drawn
                    cv2.drawContours(reveal_mask, [cnt], -1, 255, -1)
                    accumulated_cost += cost
                else:
                    # Partial draw
                    # How much of *this* contour's cost is remaining?
                    cost_in_contour = current_target_cost - accumulated_cost
                    # Fraction of this contour to show
                    fraction = max(0, min(1.0, cost_in_contour / cost))
                    
                    num_pts = len(cnt)
                    pts_to_draw = int(fraction * num_pts)
                    
                    if pts_to_draw > 0:
                         # Draw slightly thicker for visibility
                        cv2.polylines(reveal_mask, [cnt[:pts_to_draw]], False, 255, 12)
                    
                    # Stop here, we reached the current time limit
                    break
            
            # Composite
            frame = np.zeros_like(full_canvas_ref)
            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]

            return frame[:, :, ::-1]
            
            # Composite
            # 1. Background: Black
            frame = np.zeros_like(full_canvas_ref)
            
            # 2. Where Reveal Mask is White, Show the Neon Image
            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]

            return frame[:, :, ::-1] # RGB

        clip = VideoClip(make_frame, duration=self.duration)
        clip.write_videofile(self.output_path, fps=self.fps, codec='libx264', audio_codec='aac', threads=4, logger=None)
        print(f"✅ Created Neon Video: {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        img = sys.argv[1]
        vid = sys.argv[2]
        gen = NeonVideoGenerator(img, vid)
        gen.generate()
