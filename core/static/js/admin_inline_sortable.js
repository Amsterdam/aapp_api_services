(function () {
  function getSortableRows(group) {
    const body = group.querySelector("tbody");
    if (!body) {
      return [];
    }
    return Array.from(body.querySelectorAll("tr.form-row")).filter(
      (row) => !row.classList.contains("empty-form")
    );
  }

  function isDeleted(row) {
    const deleteInput = row.querySelector('input[name$="-DELETE"]');
    return !!(deleteInput && deleteInput.checked);
  }

  function reindex(group) {
    let position = 1;
    getSortableRows(group).forEach((row) => {
      if (isDeleted(row)) {
        return;
      }
      const sortInput = row.querySelector('input[name$="-sort_order"]');
      if (sortInput) {
        sortInput.value = String(position);
      }
      position += 1;
    });
  }

  function prepareRows(group) {
    const rows = getSortableRows(group);
    rows.forEach((row) => {
      if (row.dataset.sortablePrepared === "1") {
        return;
      }
      row.draggable = false;
      const handle = row.querySelector(".js-sortable-handle");
      if (handle) {
        handle.draggable = true;
        handle.style.cursor = "grab";
      }
      const deleteInput = row.querySelector('input[name$="-DELETE"]');
      if (deleteInput) {
        deleteInput.addEventListener("change", () => reindex(group));
      }
      row.dataset.sortablePrepared = "1";
    });
  }

  function getDragAfterElement(container, y) {
    const rows = Array.from(container.querySelectorAll("tr.form-row")).filter(
      (row) => !row.classList.contains("dragging") && !row.classList.contains("empty-form")
    );

    let closest = null;
    let closestOffset = Number.NEGATIVE_INFINITY;

    rows.forEach((row) => {
      const rect = row.getBoundingClientRect();
      const offset = y - (rect.top + rect.height / 2);
      if (offset < 0 && offset > closestOffset) {
        closestOffset = offset;
        closest = row;
      }
    });

    return closest;
  }

  function initGroup(group) {
    if (group.dataset.sortableInit === "1") {
      return;
    }

    const body = group.querySelector("tbody");
    if (!body) {
      return;
    }

    let draggingRow = null;
    let dropTargetRow = null;
    let dragPreview = null;

    function getCellPreviewText(cell) {
      const select = cell.querySelector("select");
      if (select && select.selectedOptions && select.selectedOptions.length > 0) {
        return Array.from(select.selectedOptions)
          .map((option) => option.textContent.trim())
          .filter(Boolean)
          .join(", ");
      }

      const textInput = cell.querySelector(
        'input[type="text"], input[type="number"], input[type="url"], input[type="email"], input[type="search"], textarea'
      );
      if (textInput && typeof textInput.value === "string") {
        const value = textInput.value.trim();
        if (value) {
          return value;
        }
      }

      const checkbox = cell.querySelector('input[type="checkbox"]');
      if (checkbox) {
        return checkbox.checked ? "yes" : "no";
      }

      const fallbackText = cell.textContent.trim();
      return fallbackText;
    }

    function createDragPreview(row) {
      const cells = Array.from(row.querySelectorAll("td"))
        .map(getCellPreviewText)
        .filter(Boolean);
      const preview = document.createElement("div");
      preview.className = "sortable-drag-preview";
      preview.textContent = cells.join("  |  ").slice(0, 140) || "Row";
      document.body.appendChild(preview);
      return preview;
    }

    function clearDropState() {
      body.classList.remove("drop-at-end");
      if (dropTargetRow) {
        dropTargetRow.classList.remove("drop-target");
      }
      dropTargetRow = null;
    }

    body.addEventListener("dragstart", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        event.preventDefault();
        return;
      }

      const handle = target.closest(".js-sortable-handle");
      if (!handle) {
        event.preventDefault();
        return;
      }
      const row = handle.closest("tr.form-row");
      if (!row || row.classList.contains("empty-form")) {
        event.preventDefault();
        return;
      }

      draggingRow = row;
      row.classList.add("dragging");
      body.classList.add("is-sorting");
      event.dataTransfer.setData("text/plain", "dragging");
      event.dataTransfer.effectAllowed = "move";
      dragPreview = createDragPreview(row);
      event.dataTransfer.setDragImage(dragPreview, 22, 18);
    });

    body.addEventListener("dragend", () => {
      if (draggingRow) {
        draggingRow.classList.remove("dragging");
      }
      if (dragPreview) {
        dragPreview.remove();
        dragPreview = null;
      }
      clearDropState();
      body.classList.remove("is-sorting");
      draggingRow = null;
      reindex(group);
    });

    body.addEventListener("dragover", (event) => {
      if (!draggingRow) {
        return;
      }
      event.preventDefault();
      const afterElement = getDragAfterElement(body, event.clientY);

      clearDropState();
      if (afterElement == null) {
        body.classList.add("drop-at-end");
        body.appendChild(draggingRow);
      } else {
        afterElement.classList.add("drop-target");
        dropTargetRow = afterElement;
        body.insertBefore(draggingRow, afterElement);
      }
    });

    body.addEventListener("drop", () => {
      clearDropState();
    });

    group.dataset.sortableInit = "1";
    prepareRows(group);
    reindex(group);
  }

  function initAll() {
    document
      .querySelectorAll('.js-inline-admin-formset[data-sortable-inline="1"]')
      .forEach(initGroup);
  }

  document.addEventListener("DOMContentLoaded", initAll);
  document.addEventListener("formset:added", (event) => {
    initAll();
    const group = event.target.closest(
      '.js-inline-admin-formset[data-sortable-inline="1"]'
    );
    if (group) {
      prepareRows(group);
      reindex(group);
    }
  });
})();