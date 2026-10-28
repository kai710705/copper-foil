import csv
import io
import zipfile
from pathlib import Path
import cv2


class InspectionTrainingExportService:
    CLASSES = ['punching','welding_line','crescent_gap','water_spot','oil_spot','silk_spot','inclusion','rolled_pit','crease','waist_fold']

    def __init__(self, repository):
        self.repository = repository

    def build_zip(self):
        records = self.repository.reviewed()
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            manifest = io.StringIO(newline='')
            writer = csv.writer(manifest)
            writer.writerow(['inspection_id', 'split', 'image_file', 'label_file', 'captured_at', 'review_status', 'annotation_count'])
            exported = 0
            for record in records:
                if record.get('annotation_status') != 'complete' or not record.get('human_annotations'):
                    continue
                source = Path(record['image_path'])
                if not source.is_file():
                    continue
                image = cv2.imread(str(source))
                if image is None:
                    continue
                height, width = image.shape[:2]
                split = 'val' if exported % 5 == 0 else 'train'
                image_name = f"{record['id']}_{source.name}"
                label_name = Path(image_name).with_suffix('.txt').name
                labels = []
                for item in record['human_annotations']:
                    name = item.get('defect_type')
                    box = item.get('box')
                    if name not in self.CLASSES or not isinstance(box, list) or len(box) != 4:
                        continue
                    x1, y1, x2, y2 = [float(value) for value in box]
                    cx=((x1+x2)/2)/width; cy=((y1+y2)/2)/height; bw=abs(x2-x1)/width; bh=abs(y2-y1)/height
                    labels.append(f'{self.CLASSES.index(name)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}')
                if not labels:
                    continue
                archive.writestr(f'images/{split}/{image_name}', source.read_bytes())
                archive.writestr(f'labels/{split}/{label_name}', '\n'.join(labels) + '\n')
                writer.writerow([record['id'], split, image_name, label_name, record['captured_at'], record['review_status'], len(labels)])
                exported += 1
            yaml = 'path: .\ntrain: images/train\nval: images/val\nnames:\n' + ''.join(f'  {i}: {name}\n' for i, name in enumerate(self.CLASSES))
            archive.writestr('data.yaml', yaml)
            archive.writestr('manifest.csv', manifest.getvalue().encode('utf-8-sig'))
        output.seek(0)
        return output
