import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class DoodleVideoGeneratorV7_2:
    """
    V7.2: Sequential Contour Drawing + Visual Grouping + Segment Sync.
    
    Fixes:
    1. Parallel Edges: Draws contours sequentially (one after another) instead of all at once.
    2. Incomplete Drawing: Strictly enforces completion of started glyphs.
    """
    
    def __init__(self, image_path, output_path, segments=None, duration=5.0, fps=24):
        self.image_path = image_path
        self.output_path = output_path
        self.segments = segments if segments else []
        self.duration = duration
        self.fps = fps
        self.width = 1920
        self.height = 1080
        self.is_dark_bg = False

    def _get_cleaned_image(self, img_bgr):
        # same as before
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
        # NOTE: Using same robust V7.1 grouping logic
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 10)) 
        dilated = cv2.dilate(ink_map, kernel, iterations=2)
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        
        groups = {}
        for g in glyphs:
            cx, cy = int(g['center'][0]), int(g['center'][1])
            cx = max(0, min(cx, ink_map.shape[1]-1))
            cy = max(0, min(cy, ink_map.shape[0]-1))
            
            group_id = labels[cy, cx]
            
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(g)
            
        meta_groups = []
        for gid, members in groups.items():
            if gid == 0 or not members:
                continue
            min_x = min(g['x'] for g in members)
            min_y = min(g['y'] for g in members)
            max_x = max(g['x']+g['w'] for g in members)
            max_y = max(g['y']+g['h'] for g in members)
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
            
        def sort_key(grp):
            y = grp['rect'][1]
            x = grp['rect'][0]
            y_bin = y // 50 
            return (y_bin, x)
            
        meta_groups.sort(key=sort_key)
        
        final_ordered_glyphs = []
        for grp in meta_groups:
            members = grp['members']
            if grp['aspect'] > 1.5:
                # Text-like: sort left-right
                members.sort(key=lambda g: g['x'])
            else:
                # Box/Diagram: sort top-down
                members.sort(key=lambda g: g['y'])
            final_ordered_glyphs.extend(members)
            
        return final_ordered_glyphs

    def generate(self):
        print(f"🎬 Processing Doodle V7.2 (Sequential+Sync) for: {self.image_path}")
        
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        original_img = cv2.imread(self.image_path)
        h, w = original_img.shape[:2]
        scale = min(self.width / w, self.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        original_resized = cv2.resize(original_img, (new_w, new_h))
        
        y_offset = (self.height - new_h) // 2
        x_offset = (self.width - new_w) // 2
        
        # 1. Cleaning
        ink_map = self._get_cleaned_image(original_resized)
        
        # 2. Glyphs
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(ink_map, connectivity=8)
        glyphs = []
        for i in range(1, num_labels):
            x, y, w_bb, h_bb, area = stats[i]
            cx, cy = x + w_bb/2, y + h_bb/2
            if area > 10:
                component_mask = (labels == i).astype(np.uint8) * 255
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    # Store contour perimeters for later
                    # Fix: Shift contours here immediately for consistency
                    shifted_contours = []
                    total_p = 0
                    for cnt in contours:
                        cnt_shift = cnt.copy()
                        cnt_shift[:, 0, 0] += x_offset
                        cnt_shift[:, 0, 1] += y_offset
                        p = cv2.arcLength(cnt_shift, True)
                        shifted_contours.append({'pts': cnt_shift, 'len': p})
                        total_p += p
                        
                    glyphs.append({
                        'id': i, 'x': x, 'y': y, 'w': w_bb, 'h': h_bb, 
                        'area': area, 
                        'contours': shifted_contours, # List of dicts {'pts':..., 'len':...}
                        'total_len': total_p,
                        'center': (cx, cy)
                    })
        
        # 3. Group
        ordered_glyphs = self._group_glyphs_spatially(ink_map, glyphs)
        
        # Prepare Canvas
        if self.is_dark_bg:
            full_canvas_ref = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            full_canvas_ref = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            
        ink_display = full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w].copy()
        mask_bool = (ink_map > 0)
        ink_display[mask_bool] = original_resized[mask_bool]
        full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = ink_display

        # --- SEGMENT TIMING ---
        segment_times = []
        if self.segments:
            sorted_segments = sorted(self.segments, key=lambda s: s.get('position', 0))
            current_time = 0.0
            for seq_idx, seg in enumerate(sorted_segments):
                seg_duration = seg.get('duration', 3.0)
                segment_times.append({
                    'section_idx': seq_idx,
                    'start': current_time,
                    'end': current_time + seg_duration
                })
                current_time += seg_duration

        num_sections = len(self.segments) if self.segments else 1
        section_width = new_w / num_sections
        
        glyph_sections = {}
        for glyph in ordered_glyphs:
            glyph_center_x = glyph['x'] + glyph['w'] / 2
            section_idx = min(int(glyph_center_x / section_width), num_sections - 1)
            if section_idx not in glyph_sections:
                glyph_sections[section_idx] = []
            glyph_sections[section_idx].append(glyph)

        def make_frame(t):
            if self.is_dark_bg:
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            else:
                frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            
            reveal_mask = np.zeros((self.height, self.width), dtype=np.uint8)
            
            if self.segments and segment_times:
                for seg_info in segment_times:
                    sec_idx = seg_info['section_idx']
                    seg_start = seg_info['start']
                    seg_end = seg_info['end']
                    
                    if sec_idx not in glyph_sections: continue
                    glyphs_in_section = glyph_sections[sec_idx]
                    if not glyphs_in_section: continue
                    
                    if t < seg_start:
                        continue
                        
                    elif t >= seg_end:
                         # Fully Draw All
                         for glyph in glyphs_in_section:
                            for c in glyph['contours']:
                                cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                                
                    else:
                        # PROGRESSIVE DRAW
                        seg_progress = (t - seg_start) / (seg_end - seg_start)
                        total_glyphs = len(glyphs_in_section)
                        current_glyph_float = total_glyphs * seg_progress
                        current_glyph_idx = int(current_glyph_float)
                        
                        # 1. Draw Completed Glyphs
                        if current_glyph_idx > 0:
                            for glyph in glyphs_in_section[:current_glyph_idx]:
                                for c in glyph['contours']:
                                    cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                        
                        # 2. Draw Active Glyph (Sequentially!)
                        if current_glyph_idx < total_glyphs:
                            active_glyph = glyphs_in_section[current_glyph_idx]
                            
                            # How much of THIS glyph to draw?
                            intra_progress = current_glyph_float - current_glyph_idx
                            target_glyph_len = active_glyph['total_len'] * intra_progress
                            
                            current_len = 0
                            for c in active_glyph['contours']:
                                c_len = c['len']
                                if current_len + c_len <= target_glyph_len:
                                    # Fully draw this contour
                                    cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                                    current_len += c_len
                                else:
                                    # Partially draw this contour
                                    needed = target_glyph_len - current_len
                                    if needed > 0 and c_len > 0:
                                        num_pts = len(c['pts'])
                                        pts_to_draw = int((needed / c_len) * num_pts)
                                        if pts_to_draw > 0:
                                            cv2.polylines(reveal_mask, [c['pts'][:pts_to_draw]], False, 255, 12)
                                    # Stop after partial draw (sequential!)
                                    break
            else:
                 reveal_mask[:] = 255

            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]
            
            return frame[:, :, ::-1]

        clip = VideoClip(make_frame, duration=self.duration)
        clip.write_videofile(
            self.output_path, fps=self.fps, codec='libx264', preset='ultrafast', audio_codec='aac', threads=4, logger=None
        )
        print(f"✅ Created V7.2 Video (SeqContours): {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        gen = DoodleVideoGeneratorV7_2(sys.argv[1], sys.argv[2], duration=5.0)
        gen.generate()
