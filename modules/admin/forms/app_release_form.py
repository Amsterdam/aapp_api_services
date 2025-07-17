from django import forms

from modules.models import AppRelease


class AppReleaseForm(forms.ModelForm):
    version_choice = forms.ChoiceField(label="Select new version")
    release = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = AppRelease
        fields = "__all__"
        widgets = {
            "version": forms.HiddenInput(),
            "release_notes": forms.Textarea(attrs={"rows": 8, "cols": 80}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["version"].required = False
        if self.instance.pk:
            self.fields["version_choice"].required = False

        release_id = self.data.get("release") or self.initial.get("release")
        release = AppRelease.objects.filter(id=release_id).first()
        base_version = release.version if release else "0.0.0"

        major, minor, patch = map(int, base_version.split("."))
        choices = [
            (f"{major + 1}.0.0", f"Bump Major to {major + 1}.0.0"),
            (f"{major}.{minor + 1}.0", f"Bump Minor to {major}.{minor + 1}.0"),
            (
                f"{major}.{minor}.{patch + 1}",
                f"Bump Patch to {major}.{minor}.{patch + 1}",
            ),
        ]
        self.fields["version_choice"].choices = choices

    def clean(self):
        cleaned = super().clean()
        # Set version to version_choice if new module_version is being created
        if not self.instance.pk:
            cleaned["version"] = cleaned.get("version_choice")
        return cleaned
