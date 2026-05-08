# services/exif_service.py
import exifread
from typing import Dict, Optional
from fractions import Fraction


class ExifService:
    TAG_MAPPING = {
        "shutter_speed": ["EXIF ShutterSpeedValue", "ExposureTime"],
        "aperture": ["EXIF ApertureValue", "EXIF FNumber"],
        "iso": ["EXIF ISOSpeedRatings"],
        "focal_length": ["EXIF FocalLength"],
        "date_taken": ["EXIF DateTimeOriginal"],
        "camera_model": ["Image Model"],
    }

    def extract(self, image_path: str) -> Dict[str, Optional[str]]:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        result = {}
        for field, tag_names in self.TAG_MAPPING.items():
            value = self._find_tag(tags, tag_names)
            result[field] = self._format_value(field, value)
        return result

    def _find_tag(self, tags: dict, tag_names: list) -> Optional[str]:
        for name in tag_names:
            if name in tags:
                return str(tags[name])
        return None

    def _format_value(self, field: str, value) -> str:
        if value is None:
            return "N/A"
        if field == "shutter_speed":
            return self._format_shutter(value)
        if field == "aperture":
            return f"f/{value}"
        if field == "focal_length":
            return self._format_focal_length(value)
        return str(value)

    def _format_shutter(self, value: str) -> str:
        try:
            if "/" in value:
                num, denom = value.split("/")
                sec = float(num) / float(denom)
                if sec < 1:
                    return f"1/{int(1/sec)}s"
                return f"{sec}s"
        except:
            pass
        return value

    def _format_focal_length(self, value: str) -> str:
        try:
            if "/" in value:
                num, denom = value.split("/")
                mm = float(num) / float(denom)
                return f"{mm:.1f}mm"
        except:
            pass
        return value