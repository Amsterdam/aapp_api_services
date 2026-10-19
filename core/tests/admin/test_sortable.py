from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.forms.models import BaseInlineFormSet
from django.test import SimpleTestCase

from core.admin.sortable import SortableInlineFormSet


class DummyForm:
    def __init__(
        self, *, pk, sort_order, submitted_sort_order, has_changed, deleted=False
    ):
        self.instance = SimpleNamespace(pk=pk, sort_order=sort_order)
        self.instance.save = MagicMock()
        self.cleaned_data = {"sort_order": submitted_sort_order, "DELETE": deleted}
        self._has_changed = has_changed

    def has_changed(self):
        return self._has_changed


def make_formset(forms, can_delete=True):
    formset = SortableInlineFormSet.__new__(SortableInlineFormSet)
    formset.sortable_field_name = "sort_order"
    formset.forms = forms
    formset.can_delete = can_delete
    formset._should_delete_form = lambda form: form.cleaned_data.get("DELETE", False)
    return formset


class TestSortableInlineFormSet(SimpleTestCase):
    def test_reordering_existing_rows_persists_for_unchanged_forms(self):
        form_a = DummyForm(
            pk=1,
            sort_order=1,
            submitted_sort_order=2,
            has_changed=False,
        )
        form_b = DummyForm(
            pk=2,
            sort_order=2,
            submitted_sort_order=1,
            has_changed=False,
        )

        formset = make_formset([form_a, form_b])

        with patch.object(
            BaseInlineFormSet, "save", return_value=["saved"]
        ) as base_save:
            saved = formset.save(commit=True)

        self.assertEqual(saved, ["saved"])
        base_save.assert_called_once_with(commit=True)

        # Normalized sorted order must follow submitted values.
        self.assertEqual(form_b.instance.sort_order, 1)
        self.assertEqual(form_a.instance.sort_order, 2)

        # Existing unchanged forms whose order changed must be explicitly saved.
        form_a.instance.save.assert_called_once_with(update_fields=["sort_order"])
        form_b.instance.save.assert_called_once_with(update_fields=["sort_order"])

    def test_adding_rows_assigns_normalized_order(self):
        existing_form = DummyForm(
            pk=10,
            sort_order=1,
            submitted_sort_order=1,
            has_changed=False,
        )
        new_form = DummyForm(
            pk=None,
            sort_order=None,
            submitted_sort_order=None,
            has_changed=True,
        )

        formset = make_formset([existing_form, new_form])

        with patch.object(
            BaseInlineFormSet, "save", return_value=["saved"]
        ) as base_save:
            formset.save(commit=True)

        base_save.assert_called_once_with(commit=True)
        self.assertEqual(existing_form.instance.sort_order, 1)
        self.assertEqual(new_form.instance.sort_order, 2)

        # New rows are persisted through BaseInlineFormSet.save; no direct save call here.
        new_form.instance.save.assert_not_called()

    def test_deleted_rows_are_excluded_and_remaining_rows_renumbered(self):
        first = DummyForm(
            pk=1,
            sort_order=1,
            submitted_sort_order=1,
            has_changed=False,
        )
        deleted = DummyForm(
            pk=2,
            sort_order=2,
            submitted_sort_order=2,
            has_changed=False,
            deleted=True,
        )
        third = DummyForm(
            pk=3,
            sort_order=3,
            submitted_sort_order=3,
            has_changed=False,
        )

        formset = make_formset([first, deleted, third])

        with patch.object(BaseInlineFormSet, "save", return_value=["saved"]):
            formset.save(commit=True)

        self.assertEqual(first.instance.sort_order, 1)
        self.assertEqual(third.instance.sort_order, 2)
        # Deleted rows are not part of active normalization.
        self.assertEqual(deleted.instance.sort_order, 2)

    def test_missing_and_duplicate_positions_are_normalized(self):
        first = DummyForm(
            pk=1,
            sort_order=8,
            submitted_sort_order=2,
            has_changed=False,
        )
        second = DummyForm(
            pk=2,
            sort_order=4,
            submitted_sort_order=2,
            has_changed=False,
        )
        third = DummyForm(
            pk=3,
            sort_order=9,
            submitted_sort_order=None,
            has_changed=False,
        )

        formset = make_formset([first, second, third])

        with patch.object(BaseInlineFormSet, "save", return_value=["saved"]):
            formset.save(commit=True)

        # Duplicate submitted values retain stable relative order.
        self.assertEqual(first.instance.sort_order, 1)
        self.assertEqual(second.instance.sort_order, 2)
        # Missing submitted values are placed last.
        self.assertEqual(third.instance.sort_order, 3)
