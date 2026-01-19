import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class ChalkVideoGenerator:
    def __init__(self, image_path, output_path, duration=5.0, drawing_duration=None, fps=24):
        self.image_path = image_path
        self.output_path = output_path
        self.duration = duration
        self.drawing_duration = drawing_duration if drawing_duration is not None else duration
        self.fps = fps
        self.width = 1920
        self.height = 1080

    def _get_sorted_contours(self, img_bgr):
        # 2. Pre-process for CHALK (White lines on Dark BG)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Use Adaptive Thresholding to create a "Sketch" look
        # STANDARD THRESH_BINARY (Not INV) because we want Bright lines to be "Foreground" (255)
        # Block Size 11, C= -2 (Negative C often helps detecting bright lines on dark)
        # Actually standard positive C with THRESH_BINARY might set the threshold below the mean?
        # Let's simple use Standard Threshold if Adaptive is finicky for "Glowing" things.
        # But let's try Adaptive with THRESH_BINARY first.
        
        binary_sketch = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -2
        )
        # Note: If background is pure black (0) and line is white (255), adaptive works well.
        
        # Clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
        cleaned = cv2.morphologyEx(binary_sketch, cv2.MORPH_OPEN, kernel)
        
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
        print(f"🎬 Processing Chalk Video (Stroke Reveal) for: {self.image_path}")
        
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
        
        ink_map, blobs_meta = self._get_sorted_contours(original_resized)
        
        raw_contours, _ = cv2.findContours(ink_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        contour_structs = []
        for cnt in raw_contours:
            area = cv2.contourArea(cnt)
            if area > 10:
                contour_structs.append({'cnt': cnt, 'area': area})
        
        # Sort logic: Same as Doodle (Text L->R, Shapes Big->Small)
        TEXT_AREA_THRESHOLD = 5000
        text_contours = []
        shape_contours = []
        
        for c in contour_structs:
            if c['area'] < TEXT_AREA_THRESHOLD:
                text_contours.append(c)
            else:
                shape_contours.append(c)
        
        shape_contours.sort(key=lambda c: c['area'], reverse=True)
        
        for tc in text_contours:
            x, y, w, h = cv2.boundingRect(tc['cnt'])
            tc['x'] = x
        text_contours.sort(key=lambda c: c['x'])
        
        sorted_contours = [c['cnt'] for c in shape_contours] + [c['cnt'] for c in text_contours]
        
        # --- BACKGROUND ---
        # BLACK Background (0)
        full_canvas_ref = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Create "Content Layer"
        # Start with Black
        ink_display_color = np.zeros_like(original_resized)
        
        # Mask where content is (ink_map > 0)
        mask_bool = (ink_map > 0)
        
        # Copy original pixels to those spots
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
        if getattr(self, 'drawing_duration', None) and self.drawing_duration < self.duration:
             target_draw_time = self.drawing_duration
             
        print(f"   ⚡ Chalk Stroke Logic: Completing in {target_draw_time:.2f}s")

        shifted_contours = []
        for cnt in sorted_contours:
            cnt_shift = cnt.copy()
            cnt_shift[:, 0, 0] += x_offset
            cnt_shift[:, 0, 1] += y_offset
            shifted_contours.append(cnt_shift)

        def make_frame(t):
            if target_draw_time <= 0: progress = 1.0
            else: progress = min(1.0, t / target_draw_time)
            
            target_len = total_perimeter * progress
            reveal_mask = np.zeros((self.height, self.width), dtype=np.uint8)
            
            current_len = 0
            
            for cnt in shifted_contours:
                p_len = cv2.arcLength(cnt, True)
                
                if current_len + p_len <= target_len:
                    cv2.drawContours(reveal_mask, [cnt], -1, 255, -1)
                    current_len += p_len
                else:
                    remaining = target_len - current_len
                    num_pts = len(cnt)
                    pts_to_draw = int((remaining / p_len) * num_pts)
                    
                    if pts_to_draw > 0:
                        # Draw thicker for Chalk
                        cv2.polylines(reveal_mask, [cnt[:pts_to_draw]], False, 255, 12)
                    break
            
            # Composite
            # Background is BLACK (zeros)
            frame = np.zeros_like(full_canvas_ref)
            
            # Where mask is active, show the chalk content
            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]

            return frame[:, :, ::-1]

        clip = VideoClip(make_frame, duration=self.duration)
        # Disable logger
        clip.write_videofile(self.output_path, fps=self.fps, codec='libx264', audio_codec='aac', threads=4, logger=None)
        print(f"✅ Created Chalk Video: {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        img = sys.argv[1]
        vid = sys.argv[2]
        gen = ChalkVideoGenerator(img, vid)
        gen.generate()
