// Custom JavaScript for Asset Management System

$(document).ready(function () {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Auto-hide alerts after 5 seconds
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Format currency input
    $('input[name="purchase_price"]').on('input', function () {
        let value = $(this).val().replace(/[^\d]/g, '');
        if (value) {
            $(this).val(parseInt(value).toLocaleString('vi-VN'));
        }
    });

    // Confirm delete via Bootstrap modal for links with data-confirm
    $(document).on('click', 'a[data-confirm]', function (e) {
        e.preventDefault();
        const href = $(this).attr('href');
        const message = $(this).data('confirm') || 'Bạn có chắc chắn muốn xóa mục này?';
        const method = ($(this).data('method') || 'get').toLowerCase();
        $('#confirmMessage').text(message);
        $('#confirmOkBtn').off('click').on('click', function (ev) {
            ev.preventDefault();
            if (method === 'post') {
                const form = $('<form>', { method: 'POST', action: href, style: 'display:none' });
                $('body').append(form);
                form.trigger('submit');
            } else {
                window.location.href = href;
            }
            $('#confirmModal').modal('hide');
        });
        $('#confirmModal').modal('show');
    });

  // Clickable small-box using data-href
  $('.small-box.clickable').css('cursor','pointer').on('click', function(e){
      var href = $(this).data('href');
      if(href){ window.location.href = href; }
  });
});

// Format number with Vietnamese locale
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Show loading spinner
function showLoading() {
    $('.loading').show();
}

// Hide loading spinner
function hideLoading() {
    $('.loading').hide();
}

// Show success message
function showSuccess(message) {
    showAlert(message, 'success');
}

// Show error message
function showError(message) {
    showAlert(message, 'danger');
}

// Show alert message
function showAlert(message, type) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
    `;
    $('.content').prepend(alertHtml);

    // Auto-hide after 5 seconds
    setTimeout(function () {
        $('.alert').fadeOut('slow');
    }, 5000);
}

// Edit category function
function editCategory(id) {
    // This would typically open a modal or redirect to edit page
    window.location.href = `/categories/edit/${id}`;
}

// Delete category function
function deleteCategory(id) {
    if (confirm('Bạn có chắc chắn muốn xóa danh mục này?')) {
        window.location.href = `/categories/delete/${id}`;
    }
}

// Edit employee function
function editEmployee(id) {
    // This would typically open a modal or redirect to edit page
    window.location.href = `/employees/edit/${id}`;
}

// Delete employee function
function deleteEmployee(id) {
    if (confirm('Bạn có chắc chắn muốn xóa nhân viên này?')) {
        window.location.href = `/employees/delete/${id}`;
    }
}

// Search functionality
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    const filter = input.value.toLowerCase();
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        const td = tr[i].getElementsByTagName("td");
        let found = false;

        for (let j = 0; j < td.length; j++) {
            if (td[j].textContent.toLowerCase().indexOf(filter) > -1) {
                found = true;
                break;
            }
        }

        tr[i].style.display = found ? "" : "none";
    }
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll("tr");
    let csv = [];

    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll("td, th");

        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/,/g, ";");
            row.push(data);
        }

        csv.push(row.join(","));
    }

    // Download CSV file
    const csvFile = new Blob([csv.join("\n")], { type: "text/csv" });
    const downloadLink = document.createElement("a");
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = "none";
    document.body.appendChild(downloadLink);
    downloadLink.click();
}

// Xóa tất cả placeholder của date input
$(document).ready(function() {
    $('.date-placeholder').remove();
});

