from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_size_bytes, field_label):
        self.max_size_bytes = max_size_bytes
        self.field_label = field_label

    def __call__(self, uploaded_file):
        if uploaded_file is None:
            return
        if uploaded_file.size > self.max_size_bytes:
            max_size_mb = self.max_size_bytes / (1024 * 1024)
            raise ValidationError(
                f"{self.field_label} no puede superar {max_size_mb:.0f} MB."
            )


@deconstructible
class MimeTypeValidator:
    def __init__(self, allowed_mime_types, field_label):
        self.allowed_mime_types = set(allowed_mime_types)
        self.field_label = field_label

    def __call__(self, uploaded_file):
        if uploaded_file is None:
            return
        detected = getattr(uploaded_file, "content_type", None)
        if detected and detected not in self.allowed_mime_types:
            allowed = ", ".join(sorted(self.allowed_mime_types))
            raise ValidationError(
                f"{self.field_label} tiene un formato no permitido ({detected}). Formatos validos: {allowed}."
            )


def validate_image_upload(uploaded_file, max_size_bytes, field_label):
    if uploaded_file is None:
        return
    MaxFileSizeValidator(max_size_bytes, field_label)(uploaded_file)