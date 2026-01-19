import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class DoodleVideoGeneratorV7:
    """
    V7.1: Visual Grouping via Dilation.
    
    Problem: Letters and diagram parts draw randomly because they are separate connected components.
    Solution:
    1. 'Dilate' (thicken) the image to merge nearby items into 'Meta-Groups' (e.g. a whole word).
    2. Sort these Groups strictly by Reading Order (or spatial logic).
    3. Draw the Group fully.
    """
    
    def __init__(self, image_path, output_path, duration=5.0, fps=24):
        self.image_path = image_path
        self.output_path = output_path
        self.duration = duration
        self.fps = fps
        self.width = 1920
        self.height = 1080
        self.is_dark_bg = False

    def _get_cleaned_image(self, img_bgr):
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        self.is_dark_bg = (mean_brightness < 127)
        thresh_type = cv2.THRESH_BINARY if self.is_dark_bg else cv2.THRESH_BINARY_INV
        binary_sketch = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, thresh_type, 11, 2
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        return cv2.morphologyEx(binary_sketch, cv2.MORPH_OPEN, kernel)

    def _group_glyphs_spatially(self, ink_map, glyphs):
        """
        Group glyphs into visual 'chunks' (words, diagram blocks) using Dilation.
        """
        # 1. Dilate to merge close items (Text lines, diagram clusters)
        # Kernel size determines 'closeness'. 
        # (15, 5) -> wide dilation to merge horizontal text, less vertical merge.
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 10)) 
        dilated = cv2.dilate(ink_map, kernel, iterations=2)
        
        # 2. Find Meta-Components (Groups)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        
        groups = {} # label_id -> list of glyphs
        
        for g in glyphs:
            # Sample the glyph's center in the dilated label map to find its group
            cx, cy = int(g['center'][0]), int(g['center'][1])
            # Bounds check
            cx = max(0, min(cx, ink_map.shape[1]-1))
            cy = max(0, min(cy, ink_map.shape[0]-1))
            
            group_id = labels[cy, cx]
            
            # If for some reason it's 0 (background), search neighborhood
            if group_id == 0:
                 # Check contour bounding box center
                 pass
            
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(g)
            
        # 3. Process Groups
        # Convert dict to list of groups, calculate group metrics
        meta_groups = []
        for gid, members in groups.items():
            if gid == 0: continue # Skip background
            if not members: continue
            
            # Calculate group bounding box
            min_x = min(g['x'] for g in members)
            min_y = min(g['y'] for g in members)
            max_x = max(g['x']+g['w'] for g in members)
            max_y = max(g['y']+g['h'] for g in members)
            
            # Determine Group Type based on Aspect Ratio / Area
            # This helps decide internal sorting
            width = max_x - min_x
            height = max_y - min_y
            aspect = width / (height + 1)
            
            meta_groups.append({
                'id': gid,
                'members': members,
                'rect': (min_x, min_y, width, height),
                'center': (min_x + width/2, min_y + height/2),
                'aspect': aspect
            })
            
        # 4. Sort Groups (Global Flow)
        # Sort by Reading Order: Top-Down primarily, Left-Right secondarily
        # To tolerate slight skew, we bin Y coordinates
        
        def sort_key(grp):
            y = grp['rect'][1]
            x = grp['rect'][0]
            # Bin Y by 50px increments to create "Lines"
            y_bin = y // 50 
            return (y_bin, x)
            
        meta_groups.sort(key=sort_key)
        
        # 5. Flatten with Internal Sort
        final_ordered_glyphs = []
        for grp in meta_groups:
            members = grp['members']
            # Internal Sort:
            # If it looks like a text line (wide aspect), sort Left-Right
            if grp['aspect'] > 1.5:
                members.sort(key=lambda g: g['x'])
            # Else (diagram blob), sort by Top-Down or Nearest Neighbor
            else:
                 members.sort(key=lambda g: g['y'])
                 
            final_ordered_glyphs.extend(members)
            
        return final_ordered_glyphs

    def generate(self):
        print(f"🎬 Processing Doodle V7.1 (Visual Grouping) for: {self.image_path}")
        
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        # Load & Resize
        original_img = cv2.imread(self.image_path)
        h, w = original_img.shape[:2]
        scale = min(self.width / w, self.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        original_resized = cv2.resize(original_img, (new_w, new_h))
        
        y_offset = (self.height - new_h) // 2
        x_offset = (self.width - new_w) // 2
        
        # Ink Map & Glyphs
        ink_map = self._get_cleaned_image(original_resized)
        
        # Find Raw Glyphs (connected parts)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(ink_map, connectivity=8)
        glyphs = []
        for i in range(1, num_labels):
            x, y, w_bb, h_bb, area = stats[i]
            cx, cy = x + w_bb/2, y + h_bb/2
            if area > 10:
                component_mask = (labels == i).astype(np.uint8) * 255
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    glyphs.append({
                        'id': i, 'x': x, 'y': y, 'w': w_bb, 'h': h_bb, 
                        'area': area, 'contours': contours,
                        'center': (cx, cy)
                    })
        
        # --- NEW LOGIC: Visual Grouping ---
        ordered_glyphs = self._group_glyphs_spatially(ink_map, glyphs)
        
        # Add any missed glyphs (if dilation failed to capture some edge cases?)
        # With this method, every glyph belongs to *some* group (label map covers all), 
        # unless it was background in the dilated map (unlikely for dilated).
        
        # Prepare Contours (Shifted)
        all_contours = []
        for g in ordered_glyphs:
            for cnt in g['contours']:
                cnt_shift = cnt.copy()
                cnt_shift[:, 0, 0] += x_offset
                cnt_shift[:, 0, 1] += y_offset
                all_contours.append(cnt_shift)
                
        # Calculate Perimeters for constant speed drawing
        total_perimeter = sum(cv2.arcLength(c, True) for c in all_contours)
        cumulative_perimeters = []
        running = 0
        for c in all_contours:
            running += cv2.arcLength(c, True)
            cumulative_perimeters.append(running)

        # Canvas Setup
        if self.is_dark_bg:
            full_canvas_ref = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            full_canvas_ref = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            
        ink_display = full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w].copy()
        mask_bool = (ink_map > 0)
        ink_display[mask_bool] = original_resized[mask_bool]
        full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = ink_display
        
        # Drawing Speed Control (Constant Speed)
        draw_duration = self.duration * 0.9 # Use 90% of time
        
        # Cache optimization
        cache_interval = max(1, len(all_contours) // 30)
        cached_masks = {}
        
        for i in range(0, len(all_contours) + 1, cache_interval):
            if i == 0:
                cached_masks[0] = np.zeros((self.height, self.width), dtype=np.uint8)
            else:
                mask = cached_masks.get(i - cache_interval, np.zeros((self.height, self.width), dtype=np.uint8)).copy()
                for j in range(i - cache_interval, min(i, len(all_contours))):
                    cv2.drawContours(mask, [all_contours[j]], -1, 255, -1)
                cached_masks[i] = mask

        def make_frame(t):
            if self.is_dark_bg:
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            else:
                frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            
            progress = min(1.0, t / draw_duration)
            target_len = total_perimeter * progress
            
            import bisect
            idx = bisect.bisect_left(cumulative_perimeters, target_len)
            
            cache_idx = (idx // cache_interval) * cache_interval
            reveal_mask = cached_masks.get(cache_idx, np.zeros((self.height, self.width), dtype=np.uint8)).copy()
            
            for j in range(cache_idx, idx):
                cv2.drawContours(reveal_mask, [all_contours[j]], -1, 255, -1)
                
            if idx < len(all_contours):
                cnt = all_contours[idx]
                prev_len = cumulative_perimeters[idx-1] if idx > 0 else 0
                needed = target_len - prev_len
                full_len = cumulative_perimeters[idx] - prev_len
                
                if full_len > 0:
                    pts = int((needed / full_len) * len(cnt))
                    if pts > 0:
                        cv2.polylines(reveal_mask, [cnt[:pts]], False, 255, 12)

            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]
            return frame[:, :, ::-1]

        clip = VideoClip(make_frame, duration=self.duration)
        clip.write_videofile(
            self.output_path, fps=self.fps, codec='libx264', preset='ultrafast', audio_codec='aac', threads=4, logger=None
        )
        print(f"✅ Created V7.1 Video (Visual Grouping): {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        # Test mode
        gen = DoodleVideoGeneratorV7(sys.argv[1], sys.argv[2], duration=5.0)
        gen.generate()
