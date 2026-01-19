import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class DoodleVideoGeneratorV6:
    """
    V6: Layout-aware / Logic-driven segmentation.
    Uses bounding boxes (from VLM) to assign glyphs to specific narrative beats.
    Allows for complex, non-linear drawing orders (e.g. center first, or specific graph elements).
    """
    
    def __init__(self, image_path, output_path, segments=None, duration=5.0, fps=24):
        """
        segments: List of dicts with:
                  - 'duration': seconds for this segment
                  - 'bbox': [ymin, xmin, ymax, xmax] (0-1000 scale) OPTIONAL
        """
        self.image_path = image_path
        self.output_path = output_path
        self.duration = duration
        self.segments = segments if segments else []
        self.fps = fps
        self.width = 1920
        self.height = 1080
        self.is_dark_bg = False

    def _get_cleaned_image(self, img_bgr):
        """Create binary ink map from image."""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Auto-detect Dark Mode
        mean_brightness = np.mean(gray)
        self.is_dark_bg = (mean_brightness < 127)
        
        thresh_type = cv2.THRESH_BINARY if self.is_dark_bg else cv2.THRESH_BINARY_INV
        
        # Adaptive Threshold for sketch look
        binary_sketch = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, thresh_type, 11, 2
        )
        
        # Clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary_sketch, cv2.MORPH_OPEN, kernel)
        
        return cleaned

    def _cluster_glyphs_by_bbox(self, glyphs, width, height, segments):
        """
        Assign glyphs to segment indices based on bounding box inclusion.
        SMART LOGIC:
        1. If a glyph is inside multiple bboxes, assign to the SMALLEST one (area).
           (This prevents 'framework' boxes from stealing all detail).
        2. If a glyph is inside NO bbox, assign to Nearest Center.
        """
        if not segments:
            return {0: glyphs}

        # Initialize bins
        segment_glyphs = {i: [] for i in range(len(segments))}
        unassigned = []
        
        # Pre-calc segment bbox areas and centers
        seg_meta = []
        for i, seg in enumerate(segments):
            bbox = seg.get('bbox') # [ymin, xmin, ymax, xmax] 0-1000
            if bbox:
                # Convert to pixels
                b_ymin = (bbox[0] / 1000.0) * height
                b_xmin = (bbox[1] / 1000.0) * width
                b_ymax = (bbox[2] / 1000.0) * height
                b_xmax = (bbox[3] / 1000.0) * width
                
                # Validation: catch bad bboxes
                if b_xmax <= b_xmin or b_ymax <= b_ymin:
                    seg_meta.append(None)
                    continue

                area = (b_ymax - b_ymin) * (b_xmax - b_xmin)
                center = ((b_xmin + b_xmax)/2, (b_ymin + b_ymax)/2)
                seg_meta.append({
                    'idx': i,
                    'rect': (b_xmin, b_ymin, b_xmax, b_ymax),
                    'area': area,
                    'center': center
                })
            else:
                seg_meta.append(None)

        for glyph in glyphs:
            # Glyph center
            gx = glyph['x'] + glyph['w'] / 2.0
            gy = glyph['y'] + glyph['h'] // 2.0
            
            best_seg_idx = -1
            min_container_area = float('inf')
            
            # 1. Find Containing BBoxes
            for meta in seg_meta:
                if not meta: continue
                
                (xmin, ymin, xmax, ymax) = meta['rect']
                
                # Check inclusion
                if xmin <= gx <= xmax and ymin <= gy <= ymax:
                    # It's inside. Is this the smallest one?
                    if meta['area'] < min_container_area:
                        min_container_area = meta['area']
                        best_seg_idx = meta['idx']
            
            if best_seg_idx != -1:
                segment_glyphs[best_seg_idx].append(glyph)
            else:
                unassigned.append(glyph)

        # 2. Distribute Unassigned (Nearest Center)
        if unassigned and segments:
            for glyph in unassigned:
                gx = glyph['x'] + glyph['w'] / 2.0
                gy = glyph['y'] + glyph['h'] // 2.0
                
                min_dist = float('inf')
                best_idx = 0
                
                # Check nearest center
                # If no valid bboxes exist at all, we might effectively be random, 
                # but VLM should give us something.
                
                valid_metas = [m for m in seg_meta if m is not None]
                if valid_metas:
                    for meta in valid_metas:
                        (cx, cy) = meta['center']
                        dist = ((gx - cx)**2 + (gy - cy)**2) ** 0.5
                        if dist < min_dist:
                            min_dist = dist
                            best_idx = meta['idx']
                    segment_glyphs[best_idx].append(glyph)
                else:
                    # No valid bboxes at all? Put in segment 0
                    segment_glyphs[0].append(glyph)
        
        # DEBUG: Print distribution
        print(f"   📊 Glyph Distribution (Smart Best-Fit):")
        for i in range(len(segments)):
            count = len(segment_glyphs[i])
            desc = segments[i].get('desc', 'N/A')
            print(f"      Seg {i} ({desc[:20]}...): {count} glyphs")
            
        return segment_glyphs

    def _sort_glyphs_in_segment(self, glyphs):
        """
        Sort glyphs within a single segment.
        Default: Top-to-bottom, Left-to-right (Raster scan).
        """
        if not glyphs: return []
        # Sort by Y (approx lines), then X
        return sorted(glyphs, key=lambda g: (g['y'] // 20, g['x'])) 

    def generate(self):
        print(f"🎬 Processing Doodle V6 (Logical-BBox) for: {self.image_path}")
        
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        # 1. Load Image
        original_img = cv2.imread(self.image_path)
        if original_img is None:
            raise ValueError(f"Could not load image: {self.image_path}")
            
        # 2. Resize Logic (Fit to 1080p, preserving aspect ratio)
        h, w = original_img.shape[:2]
        scale = min(self.width / w, self.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        original_resized = cv2.resize(original_img, (new_w, new_h))
        
        y_offset = (self.height - new_h) // 2
        x_offset = (self.width - new_w) // 2
        
        # 3. Get Ink Map
        ink_map = self._get_cleaned_image(original_resized)
        
        # 4. Use Connected Components to find "glyphs"
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(ink_map, connectivity=8)
        
        glyphs = []
        for i in range(1, num_labels):
            x, y, w_bb, h_bb, area = stats[i]
            if area > 10:
                component_mask = (labels == i).astype(np.uint8) * 255
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    glyphs.append({
                        'id': i,
                        'x': x, 'y': y, 'w': w_bb, 'h': h_bb,
                        'area': area,
                        'contours': contours
                    })
        
        print(f"   📊 Found {len(glyphs)} glyphs")
        
        # 5. Cluster glyphs into explicit segments
        segment_glyph_map = self._cluster_glyphs_by_bbox(glyphs, new_w, new_h, self.segments)
        
        # 6. Build Ordered List for Rendering
        ordered_glyphs = []
        glyph_sections = {} # Map section_idx -> list of glyph units (for reveal)
        
        num_segments = len(self.segments) if self.segments else 1
        
        for i in range(num_segments):
            seg_glyphs = segment_glyph_map.get(i, [])
            sorted_seg_glyphs = self._sort_glyphs_in_segment(seg_glyphs)
            
            if i not in glyph_sections:
                glyph_sections[i] = []
            
            for g in sorted_seg_glyphs:
                ordered_glyphs.append(g)
                # Prepare contours for section reveal
                shifted_contours = []
                for cnt in g['contours']:
                    cnt_shift = cnt.copy()
                    cnt_shift[:, 0, 0] += x_offset
                    cnt_shift[:, 0, 1] += y_offset
                    shifted_contours.append(cnt_shift)
                
                glyph_sections[i].append({
                    'contours': shifted_contours,
                    'id': g['id']
                })
        
        # 8. Setup Canvas
        if self.is_dark_bg:
            full_canvas_ref = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            full_canvas_ref = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        
        ink_display_color = full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w].copy()
        mask_bool = (ink_map > 0)
        ink_display_color[mask_bool] = original_resized[mask_bool]
        full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = ink_display_color
        
        # 9. Timing Setup
        segment_times = []
        if self.segments:
            current_time = 0.0
            for seq_idx, seg in enumerate(self.segments):
                seg_duration = seg.get('duration', 3.0)
                segment_times.append({
                    'section_idx': seq_idx,
                    'start': current_time,
                    'end': current_time + seg_duration
                })
                current_time += seg_duration
            print(f"   📊 Segment reveal: {len(segment_times)} segments, total time {current_time:.2f}s")
        
        # 10. Frame Generator
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
                    
                    glyphs_in_section = glyph_sections.get(sec_idx, [])
                    if not glyphs_in_section: continue
                    
                    if t >= seg_end:
                        # Fully revealed
                        for glyph_unit in glyphs_in_section:
                            for cnt in glyph_unit['contours']:
                                cv2.drawContours(reveal_mask, [cnt], -1, 255, -1)
                    elif t >= seg_start:
                        # Partial reveal
                        seg_progress = (t - seg_start) / (seg_end - seg_start) 
                        segs_to_show = int(len(glyphs_in_section) * seg_progress)
                        # Draw full glyphs up to progress
                        for glyph_unit in glyphs_in_section[:segs_to_show]:
                             for cnt in glyph_unit['contours']:
                                cv2.drawContours(reveal_mask, [cnt], -1, 255, -1)
            else:
                 pass 

            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]
            return frame[:, :, ::-1]

        clip = VideoClip(make_frame, duration=self.duration)
        clip.write_videofile(
            self.output_path,
            fps=self.fps, 
            codec='libx264', preset='ultrafast', audio_codec='aac', threads=4, logger=None
        )
        print(f"✅ Created Doodle V6: {self.output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        img = sys.argv[1]
        vid = sys.argv[2]
        segs = [{'bbox': [0, 0, 1000, 1000], 'duration': 4.0}]
        gen = DoodleVideoGeneratorV6(img, vid, segments=segs, duration=4.0)
        gen.generate()
