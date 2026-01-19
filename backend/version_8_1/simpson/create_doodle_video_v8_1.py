import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class DoodleVideoGeneratorV8_1:
    """
    V8.1: Talking Characters (V7.4 Base + Lip Sync)
    
    Logic:
    1. Base: EXACTLY V7.3 (Safe Merge + Nearest Neighbor).
    2. Fix: Starts Nearest Neighbor from Top-Left (not Largest) to ensure L->R flow.
    3. Style: Adds 'solid', 'normal', 'pencil' modes (affects thresholding only).
    """
    
    def __init__(self, image_path, output_path, segments=None, duration=5.0, fps=24, style='normal', pps=4000):
        self.image_path = image_path
        self.output_path = output_path
        self.segments = segments if segments else []
        self.duration = duration
        self.fps = fps
        self.style = style # 'normal', 'solid', 'pencil'
        self.pps = pps # Pixels Per Second (Speed of drawing)
        self.width = 1920
        self.height = 1080
        self.is_dark_bg = False

    def _get_cleaned_image(self, img_bgr):
        # 1. Grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        self.is_dark_bg = (mean_brightness < 127)
        thresh_type = cv2.THRESH_BINARY if self.is_dark_bg else cv2.THRESH_BINARY_INV
        
        # 2. Style Logic
        if self.style == 'solid':
            # Solid: Otsu's Thresholding (Clean, strict binary)
            # Use minimal blur before otsu
            blurred = cv2.GaussianBlur(gray, (3,3), 0)
            _, binary = cv2.threshold(blurred, 0, 255, thresh_type + cv2.THRESH_OTSU)
            return binary
            
        else: # 'normal' or 'pencil'
            # Normal/Pencil: Adaptive Thresholding (Preserves texture/sketchiness)
            binary_sketch = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, thresh_type, 11, 2
            )
            # Clean tiny noise
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            return cv2.morphologyEx(binary_sketch, cv2.MORPH_OPEN, kernel)

    def _sort_contours_by_path(self, glyphs):
        """
        Sort Strategy (V8.4):
        1. Macro Objects (Characters, Bubble Outlines) -> Sort by AREA (Largest First).
        2. Micro Objects (Text, Details) -> Sort Spatially (Top-Left to Bottom-Right).
        """
        if not glyphs: return []
        
        # Threshold to distinguish "Main Objects" from "Details/Text"
        MACRO_THRESHOLD = 5000 
        
        macro_objs = []
        micro_objs = []
        
        for g in glyphs:
            if g['area'] >= MACRO_THRESHOLD:
                macro_objs.append(g)
            else:
                micro_objs.append(g)
                
        # 1. Macro Sort: Largest Area First
        macro_objs.sort(key=lambda g: g['area'], reverse=True)
        
        # 2. Micro Sort: Spatial (Reading Order)
        y_sorted = sorted(micro_objs, key=lambda g: g['y'])
        lines = [] 
        
        for g in y_sorted:
            best_line_idx = -1
            g_cy = g['center'][1]
            g_h = g['h']
            
            for idx, line in enumerate(lines):
                l_avg_cy = sum(item['center'][1] for item in line) / len(line)
                if abs(g_cy - l_avg_cy) < (max(g_h, 30) * 1.5): 
                    best_line_idx = idx
                    break
            
            if best_line_idx != -1:
                lines[best_line_idx].append(g)
            else:
                lines.append([g])
                
        lines.sort(key=lambda line: sum(item['y'] for item in line) / len(line))
        
        sorted_micro = []
        for line in lines:
            line.sort(key=lambda item: item['x'])
            sorted_micro.extend(line)
            
        return macro_objs + sorted_micro

    def _safely_merge_words(self, glyphs):
        """
        Safely merge small, close components (letters) into Words.
        Relaxed thresholds to catch more letters.
        """
        if not glyphs: return []
        
        candidates = []
        bypass = []
        
        for g in glyphs:
            if g['area'] < 10000: # Slightly increased area threshold
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
            
            # Vertical: Must be roughly on same line
            # Relaxed from 0.5 to 0.7
            vertical_match = abs(cy1 - cy2) < (avg_h * 0.7) 
            
            # Horizontal: Must be close (Kerning)
            r1 = current_meta['x'] + current_meta['w']
            l2 = next_g['x']
            gap = l2 - r1
            
            # Relaxed Gap: allow gap up to 1.2x height (was 0.4)
            # This catches spaces between letters even in loose handwriting
            horizontal_match = gap < (avg_h * 1.2) and gap > -(avg_h * 0.5)
            
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
        return merged + bypass

    def generate(self):
        print(f"🎬 Processing Doodle V7.4 ({self.style}, TopLeft Start) for: {self.image_path}")
        
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
        # Logic: Only segments with 'draw'=True get glyphs.
        # This allows "Draw Everything First" (Segment 0) then "Static Talk" (Segment 1..N)
        
        drawing_segments = [i for i, s in enumerate(self.segments) if s.get('draw', True)]
        num_sections = len(drawing_segments)
        if num_sections == 0: num_sections = 1 # Fallback
        
        section_width = new_w / num_sections
        
        glyph_sections = {}
        for glyph in glyphs:
            glyph_center_x = glyph['x'] + glyph['w'] / 2
            
            # Map to visual section (spatial)
            spatial_sec_idx = min(int(glyph_center_x / section_width), num_sections - 1)
            
            # Map spatial section to the ACTUAL segment index that handles it
            target_segment_idx = drawing_segments[spatial_sec_idx]
            
            if target_segment_idx not in glyph_sections:
                glyph_sections[target_segment_idx] = []
            glyph_sections[target_segment_idx].append(glyph)
            
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
            # Keep original order, just map times
            current_time = 0.0
            for seq_idx, seg in enumerate(self.segments):
                seg_duration = seg.get('duration', 3.0)
                segment_times.append({
                    'section_idx': seq_idx, # Index matches self.segments
                    'start': current_time,
                    'end': current_time + seg_duration,
                    'draw': seg.get('draw', True)
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
                    is_drawing_segment = seg_info['draw']
                    
                    # 1. VISIBLE?
                    # If this segment is ALREADY DONE (t >= seg_end), always draw its glyphs fully
                    # (Unless it wasn't a drawing segment, in which case it has no glyphs)
                    
                    # If this segment is ACTIVE (start <= t < end):
                    #   If drawing=True: Draw Progressively
                    #   If drawing=False: Draw Fully (Static) - wait, glyphs are assigned to segments.
                    #   If a segment has NO glyphs assigned (Dialogue), it just shows previous stuff.
                    
                    # Mapping:
                    # We iteration over ALL segments (past and present).
                    
                    draw_full = False
                    draw_partial = False
                    progress = 0.0
                    
                    if t >= seg_end:
                        draw_full = True
                    elif t >= seg_start:
                        # Current segment
                        if is_drawing_segment:
                            draw_partial = True
                            progress = (t - seg_start) / (seg_end - seg_start)
                        else:
                            # It's a static/talking segment. 
                            # It has no glyphs mapped to it?
                            # If it DOES have glyphs (unlikely in this logic), draw them fully?
                            # Actually, glyphs are mapped only to 'drawing' segments.
                            draw_full = True # Just in case
                    else:
                        # Future segment
                        continue 
                        
                    # Retrieve Glyph Content
                    if sec_idx not in glyph_sections: continue
                    glyphs_in_section = glyph_sections[sec_idx] 
                    if not glyphs_in_section: continue
                    
                    if draw_full:
                        # Draw everything
                         for glyph in glyphs_in_section:
                            for c in glyph['contours']:
                                cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                                
                    elif draw_partial:
                        # PROGRESSIVE DRAW (Constant Speed - PPS)
                        # Decoupled from Duration!
                        
                        # 1. Calculate Total Section Length
                        total_section_len = sum(g['total_len'] for g in glyphs_in_section)
                        if total_section_len == 0: total_section_len = 1
                        
                        # 2. Calculate Target Length based on Speed (PPS)
                        time_elapsed = t - seg_start
                        # Linear speed: pixels = speed * time
                        target_len = min(total_section_len, time_elapsed * self.pps)
                        
                        current_drawn_len = 0
                        
                        for glyph in glyphs_in_section:
                            g_len = glyph['total_len']
                            
                            # If we can fully draw this glyph
                            if current_drawn_len + g_len <= target_len:
                                for c in glyph['contours']:
                                    cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                                current_drawn_len += g_len
                                
                            else:
                                # Partial Draw of this glyph
                                needed_for_glyph = target_len - current_drawn_len
                                
                                if needed_for_glyph > 0:
                                    # Normalize to glyph progress (0..1)
                                    glyph_ratio = needed_for_glyph / g_len
                                    target_glyph_len = g_len * glyph_ratio
                                    
                                    curr_c_len = 0
                                    for c in glyph['contours']:
                                        c_len = c['len']
                                        if curr_c_len + c_len <= target_glyph_len:
                                            cv2.drawContours(reveal_mask, [c['pts']], -1, 255, -1)
                                            curr_c_len += c_len
                                        else:
                                            # Partial contour
                                            needed_pts_len = target_glyph_len - curr_c_len
                                            if needed_pts_len > 0 and c_len > 0:
                                                num_pts = len(c['pts'])
                                                pts_to_draw = int((needed_pts_len / c_len) * num_pts)
                                                if pts_to_draw > 0:
                                                     cv2.polylines(reveal_mask, [c['pts'][:pts_to_draw]], False, 255, 12)
                                            break
                                break # Stop after partial glyph
            else:
                 reveal_mask[:] = 255

            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]
            
            return frame[:, :, ::-1]

        clip = VideoClip(make_frame, duration=self.duration)
        clip.write_videofile(
            self.output_path, fps=self.fps, codec='libx264', preset='ultrafast', audio_codec='aac', threads=4, logger=None
        )
        print(f"✅ Created V7.4 Video (Style={self.style}, TopLeft Start): {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        # Defaults
        dur = 5.0
        style = 'normal'
        
        # Simple arg parsing
        if len(sys.argv) > 3:
            # Check if 3rd arg is float (dur) or str (style)
            try:
                dur = float(sys.argv[3])
                if len(sys.argv) > 4:
                    style = sys.argv[4]
            except ValueError:
                style = sys.argv[3]
                
        gen = DoodleVideoGeneratorV8_1(sys.argv[1], sys.argv[2], duration=dur, style=style)
        gen.generate()
