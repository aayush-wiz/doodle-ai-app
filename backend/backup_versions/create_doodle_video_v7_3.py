import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class DoodleVideoGeneratorV7_3:
    """
    V7.3 (Pen Trace Edition): V7.2 Base + Nearest Neighbor Pathing.
    
    Logic:
    1. Base: Uses V7.2's reliable Sequential Contour Drawing (fixes Parallel Edges).
    2. Sorting: Nearest Neighbor Chaining.
       - Starts at largest element (Anchor).
       - Moves to nearest unvisited element.
       - Simulates natural hand travel.
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

    def _sort_contours_by_path(self, glyphs):
        """
        Sort glyphs/contours by simulating a pen travelling to the nearest neighbor.
        """
        if not glyphs: return []
        
        # 1. Start with the "Most Significant" glyph (Largest Area)
        # Optimization: Start with Largest Area Glyph.
        start_idx = max(range(len(glyphs)), key=lambda i: glyphs[i]['area'])
        
        ordered = [glyphs[start_idx]]
        unvisited = list(glyphs)
        unvisited.pop(start_idx)
        
        current = ordered[0]
        
        # 2. Greedy Nearest Neighbor
        while unvisited:
            cx, cy = current['center']
            
            # Find closest in unvisited
            best_idx = -1
            min_dist = float('inf')
            
            for i, cand in enumerate(unvisited):
                dcx, dcy = cand['center']
                dist = (cx - dcx)**2 + (cy - dcy)**2
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i
            
            next_glyph = unvisited.pop(best_idx)
            ordered.append(next_glyph)
            current = next_glyph
            
        return ordered

    def _safely_merge_words(self, glyphs):
        """
        Safely merge small, close components (letters) into Words.
        Strict thresholds prevent merging diagrams.
        """
        if not glyphs: return []
        
        # 1. Separate "Likely Text" (Small Area) from "Likely Diagram" (Large Area)
        # Using a dynamic threshold or fixed? 
        # Letters are usually small.
        # Let's use a conservative threshold: 1% of screen size? 
        # 1920*1080 = 2M. 1% = 20k pixels. That's huge.
        # A letter 'A' might be 50x50 = 2500 px.
        # Let's say Area < 8000.
        
        candidates = []
        bypass = []
        
        for g in glyphs:
            if g['area'] < 8000:
                candidates.append(g)
            else:
                bypass.append(g)
                
        if not candidates: return bypass
        
        # Sort candidates for merging
        candidates.sort(key=lambda g: (g['y'], g['x']))
        
        merged = []
        current_meta = candidates[0]
        
        for next_g in candidates[1:]:
            cy1 = current_meta['center'][1]
            cy2 = next_g['center'][1]
            h1 = current_meta['h']
            h2 = next_g['h']
            avg_h = (h1 + h2) / 2
            
            # STRICT Vertical: Must be on same line
            vertical_match = abs(cy1 - cy2) < (avg_h * 0.5) 
            
            # STRICT Horizontal: Must be very close (Kerning)
            # Gap < 0.3 * Height
            r1 = current_meta['x'] + current_meta['w']
            l2 = next_g['x']
            gap = l2 - r1
            
            horizontal_match = gap < (avg_h * 0.4) and gap > -(avg_h * 0.2)
            
            if vertical_match and horizontal_match:
                # MERGE
                new_x = min(current_meta['x'], next_g['x'])
                new_y = min(current_meta['y'], next_g['y'])
                new_r = max(current_meta['x'] + current_meta['w'], next_g['x'] + next_g['w'])
                new_b = max(current_meta['y'] + current_meta['h'], next_g['y'] + next_g['h'])
                
                current_meta['x'] = new_x
                current_meta['y'] = new_y
                current_meta['w'] = new_r - new_x
                current_meta['h'] = new_b - new_y
                current_meta['area'] += next_g['area']
                current_meta['center'] = (new_x + current_meta['w']/2, new_y + current_meta['h']/2)
                current_meta['contours'].extend(next_g['contours'])
                current_meta['total_len'] += next_g['total_len']
            else:
                merged.append(current_meta)
                current_meta = next_g
        
        merged.append(current_meta)
        
        # Combine back with bypass and return
        final_list = merged + bypass
        return final_list

    def generate(self):
        print(f"🎬 Processing Doodle V7.3 (PenTrace + SafeMerge) for: {self.image_path}")
        
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
        
        # 2. Extract Glyphs (Atomic parts)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(ink_map, connectivity=8)
        glyphs = []
        for i in range(1, num_labels):
            x, y, w_bb, h_bb, area = stats[i]
            cx, cy = x + w_bb/2, y + h_bb/2
            if area > 10:
                component_mask = (labels == i).astype(np.uint8) * 255
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
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
                        'contours': shifted_contours, 
                        'total_len': total_p,
                        'center': (cx, cy)
                    })
        
        # 3. SEGMENT & SORT FILTERING
        num_sections = len(self.segments) if self.segments else 1
        section_width = new_w / num_sections
        
        glyph_sections = {}
        for glyph in glyphs:
            glyph_center_x = glyph['x'] + glyph['w'] / 2 
            section_idx = min(int(glyph_center_x / section_width), num_sections - 1)
            if section_idx not in glyph_sections:
                glyph_sections[section_idx] = []
            glyph_sections[section_idx].append(glyph)
            
        # 4. PROCESS EACH SECTION
        for sec_idx, g_list in glyph_sections.items():
            # A. SAFE MERGE (Atomic Words)
            merged_glyphs = self._safely_merge_words(g_list)
            
            # B. SORT BY PEN PATH
            sorted_glyphs = self._sort_contours_by_path(merged_glyphs)
            
            glyph_sections[sec_idx] = sorted_glyphs

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
                        
                        # 2. Draw Active Glyph
                        if current_glyph_idx < total_glyphs:
                            active_glyph = glyphs_in_section[current_glyph_idx]
                            
                            intra_progress = current_glyph_float - current_glyph_idx
                            target_glyph_len = active_glyph['total_len'] * intra_progress
                            
                            current_len = 0
                            for c in active_glyph['contours']:
                                c_len = c['len']
                                if current_len + c_len <= target_glyph_len:
                                    cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                                    current_len += c_len
                                else:
                                    needed = target_glyph_len - current_len
                                    if needed > 0 and c_len > 0:
                                        num_pts = len(c['pts'])
                                        pts_to_draw = int((needed / c_len) * num_pts)
                                        if pts_to_draw > 0:
                                            cv2.polylines(reveal_mask, [c['pts'][:pts_to_draw]], False, 255, 12)
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
        print(f"✅ Created V7.3 Video (PenTrace): {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        gen = DoodleVideoGeneratorV7_3(sys.argv[1], sys.argv[2], duration=5.0)
        gen.generate()
