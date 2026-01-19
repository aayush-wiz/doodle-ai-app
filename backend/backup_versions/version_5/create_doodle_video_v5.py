import cv2
import numpy as np
from moviepy.editor import VideoClip
import os

class DoodleVideoGeneratorV5:
    """
    V5: Pure algorithmic approach - NO VLM segmentation.
    Uses grid-based row clustering for proper left-to-right, top-to-bottom reading order.
    Optimized for simple horizontal layouts.
    """
    
    def __init__(self, image_path, output_path, segments=None, duration=5.0, fps=24):
        """
        segments: Optional list of dicts with 'duration' keys.
                  If provided, drawing is chunked into timed sections.
        """
        self.image_path = image_path
        self.output_path = output_path
        self.duration = duration
        self.segments = segments if segments else []
        self.fps = fps
        self.width = 1920
        self.height = 1080

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

    def _cluster_into_grid_rows(self, glyphs, img_height):
        """
        Cluster glyphs into rows using a fixed grid approach.
        Divides image into horizontal bands and assigns glyphs to bands.
        Then sorts left-to-right within each band.
        """
        if not glyphs:
            return []
        
        # Calculate dynamic row height: divide image into ~10-20 rows
        # Or use the median glyph height as reference
        heights = [g['h'] for g in glyphs if g['h'] > 5]
        if heights:
            median_h = np.median(heights)
            # Row height = 2x median glyph height (to group letters on same line)
            row_height = max(30, int(median_h * 2.5))
        else:
            row_height = max(30, img_height // 15)
        
        print(f"      Using row height: {row_height}px")
        
        # Assign each glyph to a row band based on its center Y
        row_assignments = {}
        for g in glyphs:
            center_y = g['y'] + g['h'] // 2
            row_idx = center_y // row_height
            if row_idx not in row_assignments:
                row_assignments[row_idx] = []
            row_assignments[row_idx].append(g)
        
        # Sort rows by row index (top to bottom)
        sorted_row_indices = sorted(row_assignments.keys())
        
        rows = []
        for row_idx in sorted_row_indices:
            row_glyphs = row_assignments[row_idx]
            # Sort left-to-right by X position
            row_glyphs.sort(key=lambda g: g['x'])
            rows.append(row_glyphs)
        
        return rows

    def generate(self):
        print(f"🎬 Processing Doodle V5 (Grid-Row) for: {self.image_path}")
        
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found: {self.image_path}")

        # 1. Load Image
        original_img = cv2.imread(self.image_path)
        if original_img is None:
            raise ValueError(f"Could not load image: {self.image_path}")
            
        # 2. Resize Logic (Fit to 1080p)
        h, w = original_img.shape[:2]
        scale = min(self.width / w, self.height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        original_resized = cv2.resize(original_img, (new_w, new_h))
        
        y_offset = (self.height - new_h) // 2
        x_offset = (self.width - new_w) // 2
        
        # 3. Get Ink Map
        ink_map = self._get_cleaned_image(original_resized)
        
        # 4. Use Connected Components to find "glyphs" (blobs)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(ink_map, connectivity=8)
        
        # Build glyph info
        glyphs = []
        for i in range(1, num_labels):  # Skip 0 (background)
            x, y, w_bb, h_bb, area = stats[i]
            if area > 10:  # Filter noise
                # Create a mask for this component
                component_mask = (labels == i).astype(np.uint8) * 255
                # Find contours for this component
                contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    glyphs.append({
                        'id': i,
                        'x': x,
                        'y': y,
                        'w': w_bb,
                        'h': h_bb,
                        'area': area,
                        'contours': contours,
                        'perimeter': sum(cv2.arcLength(c, True) for c in contours)
                    })
        
        print(f"   📊 Found {len(glyphs)} glyphs")
        
        # 5. Cluster into rows using grid-based approach
        rows = self._cluster_into_grid_rows(glyphs, new_h)
        print(f"   📊 Clustered into {len(rows)} rows")
        
        # 6. Flatten rows into ordered glyph list
        ordered_glyphs = []
        for row in rows:
            ordered_glyphs.extend(row)
        
        # 7. Shift contours to canvas coordinates and flatten
        all_contours = []
        total_perimeter = 0
        
        for glyph in ordered_glyphs:
            for cnt in glyph['contours']:
                cnt_shift = cnt.copy()
                cnt_shift[:, 0, 0] += x_offset
                cnt_shift[:, 0, 1] += y_offset
                all_contours.append(cnt_shift)
                total_perimeter += cv2.arcLength(cnt, True)
        
        print(f"   📊 Total contours: {len(all_contours)}, Total perimeter: {total_perimeter:.0f}px")
        
        # 8. Setup Canvas
        if self.is_dark_bg:
            full_canvas_ref = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        else:
            full_canvas_ref = np.ones((self.height, self.width, 3), dtype=np.uint8) * 255
        
        # Place ink on canvas (preserve original colors)
        ink_display_color = full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w].copy()
        mask_bool = (ink_map > 0)
        ink_display_color[mask_bool] = original_resized[mask_bool]
        full_canvas_ref[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = ink_display_color
        
        # 9. Calculate drawing time - FAST DRAW (max 5 seconds), rest is hold time
        # This ensures the doodle draws quickly, then holds for viewing
        drawing_time = min(5.0, self.duration * 0.4)  # Max 5s or 40% of duration
        print(f"   ⚡ Drawing time: {drawing_time:.2f}s (total duration: {self.duration:.2f}s)")
        
        # 10. Pre-compute cumulative perimeters for fast lookup
        cumulative_perimeters = []
        running_sum = 0
        for cnt in all_contours:
            running_sum += cv2.arcLength(cnt, True)
            cumulative_perimeters.append(running_sum)
        
        # 11. Pre-compute cached masks for every N contours (cache every 50 contours)
        cache_interval = max(1, len(all_contours) // 20)  # ~20 cache points
        cached_masks = {}
        
        for cache_idx in range(0, len(all_contours) + 1, cache_interval):
            if cache_idx == 0:
                cached_masks[0] = np.zeros((self.height, self.width), dtype=np.uint8)
            else:
                # Build mask up to this point
                mask = cached_masks.get(cache_idx - cache_interval, np.zeros((self.height, self.width), dtype=np.uint8)).copy()
                for j in range(cache_idx - cache_interval, min(cache_idx, len(all_contours))):
                    cv2.drawContours(mask, [all_contours[j]], -1, 255, -1)
                cached_masks[cache_idx] = mask
        
        print(f"   ⚡ Pre-computed {len(cached_masks)} mask cache points")
        
        # 12. Calculate segment timing for progressive reveal
        # If segments provided, reveal portions of image progressively
        segment_times = []
        if self.segments:
            # Sort segments by position to ensure left-to-right order
            sorted_segments = sorted(self.segments, key=lambda s: s.get('position', 0))
            
            # Build time windows - use SEQUENTIAL index (0, 1, 2) not manifest position
            current_time = 0.0
            for seq_idx, seg in enumerate(sorted_segments):
                seg_duration = seg.get('duration', 3.0)
                segment_times.append({
                    'section_idx': seq_idx,  # Sequential section index for glyph matching
                    'manifest_pos': seg.get('position', 0),  # Original position (for debugging)
                    'start': current_time,
                    'end': current_time + seg_duration
                })
                current_time += seg_duration
            print(f"   📊 Segment reveal: {len(segment_times)} segments")
        
        # Group glyphs by horizontal position - sections MUST match segment count
        # With 2 segments: divide image into 2 halves (left, right)
        # With 3 segments: divide image into 3 thirds (left, center, right)
        num_sections = len(self.segments) if self.segments else 1
        section_width = new_w / num_sections
        
        # Assign each glyph to a SEQUENTIAL section index (0, 1, 2...) based on X position
        glyph_sections = {}
        for glyph in ordered_glyphs:
            glyph_center_x = glyph['x'] + glyph['w'] / 2
            section_idx = min(int(glyph_center_x / section_width), num_sections - 1)
            if section_idx not in glyph_sections:
                glyph_sections[section_idx] = []
            # Store shifted contours for this glyph as a unit
            shifted_contours = []
            for cnt in glyph['contours']:
                cnt_shift = cnt.copy()
                cnt_shift[:, 0, 0] += x_offset
                cnt_shift[:, 0, 1] += y_offset
                shifted_contours.append(cnt_shift)
            glyph_sections[section_idx].append({
                'contours': shifted_contours,  # All contours for this glyph
                'id': glyph['id']
            })
        
        def make_frame(t):
            # Create frame
            if self.is_dark_bg:
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            else:
                frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            
            reveal_mask = np.zeros((self.height, self.width), dtype=np.uint8)
            
            if self.segments and segment_times:
                # Progressive segment reveal mode - draw complete glyphs
                for seg_info in segment_times:
                    sec_idx = seg_info['section_idx']  # Use sequential index, not manifest position
                    seg_start = seg_info['start']
                    seg_end = seg_info['end']
                    
                    if sec_idx not in glyph_sections:
                        continue
                    
                    glyphs_in_section = glyph_sections[sec_idx]
                    if not glyphs_in_section:
                        continue
                    
                    if t < seg_start:
                        # Not started yet - don't reveal this section
                        continue
                    elif t >= seg_end:
                        # Fully revealed - draw all glyphs in this section
                        for glyph_unit in glyphs_in_section:
                            for cnt in glyph_unit['contours']:
                                cv2.drawContours(reveal_mask, [cnt], -1, 255, -1)
                    else:
                        # Partial reveal - reveal COMPLETE glyphs only (no partial)
                        seg_progress = (t - seg_start) / (seg_end - seg_start)
                        num_glyphs_to_reveal = int(len(glyphs_in_section) * seg_progress) + 1
                        
                        # Draw complete glyphs
                        for glyph_unit in glyphs_in_section[:num_glyphs_to_reveal]:
                            for cnt in glyph_unit['contours']:
                                cv2.drawContours(reveal_mask, [cnt], -1, 255, -1)
            else:
                # Fallback: simple linear reveal (original mode)
                if drawing_time <= 0:
                    progress = 1.0
                else:
                    progress = min(1.0, t / drawing_time)
                
                target_len = total_perimeter * progress
                
                # Binary search to find cutoff
                left, right = 0, len(cumulative_perimeters)
                while left < right:
                    mid = (left + right) // 2
                    if cumulative_perimeters[mid] <= target_len:
                        left = mid + 1
                    else:
                        right = mid
                
                # Find nearest cached mask
                cache_point = (left // cache_interval) * cache_interval
                if cache_point in cached_masks:
                    reveal_mask = cached_masks[cache_point].copy()
                else:
                    cache_point = 0
                
                # Draw remaining completed contours
                for j in range(cache_point, left):
                    cv2.drawContours(reveal_mask, [all_contours[j]], -1, 255, -1)
                
                # Draw partial contour
                if left < len(all_contours):
                    cnt = all_contours[left]
                    prev_len = cumulative_perimeters[left - 1] if left > 0 else 0
                    remaining = target_len - prev_len
                    p_len = cumulative_perimeters[left] - prev_len
                    
                    if p_len > 0 and remaining > 0:
                        num_pts = len(cnt)
                        pts_to_draw = int((remaining / p_len) * num_pts)
                        if pts_to_draw > 0:
                            cv2.polylines(reveal_mask, [cnt[:pts_to_draw]], False, 255, 12)
            
            # Composite
            mask_bool = (reveal_mask > 0)
            frame[mask_bool] = full_canvas_ref[mask_bool]
            
            return frame[:, :, ::-1]  # BGR to RGB

        # 13. Generate video
        clip = VideoClip(make_frame, duration=self.duration)
        clip.write_videofile(
            self.output_path,
            fps=self.fps,
            codec='libx264',
            preset='ultrafast',
            audio_codec='aac',
            threads=8,
            logger=None
        )
        print(f"✅ Created Doodle V5: {self.output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        img = sys.argv[1]
        vid = sys.argv[2]
        dur = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
        gen = DoodleVideoGeneratorV5(img, vid, duration=dur)
        gen.generate()
