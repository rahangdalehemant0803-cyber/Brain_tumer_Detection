document.addEventListener("DOMContentLoaded", () => {

  // ---------------- Upload dropzone (dashboard page) ----------------
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("mri_image");
  const previewWrap = document.getElementById("dropzone-preview");
  const previewImg = document.getElementById("preview-img");
  const submitBtn = document.getElementById("analyze-btn");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    ["dragenter", "dragover"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length) {
        fileInput.files = files;
        showPreview(files[0]);
      }
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files[0]) {
        showPreview(fileInput.files[0]);
      }
    });

    function showPreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        dropzone.querySelector(".dz-empty-state").style.display = "none";
        previewWrap.style.display = "block";
        previewWrap.classList.add("scanning");
        if (submitBtn) submitBtn.disabled = false;
      };
      reader.readAsDataURL(file);
    }
  }

  // when the analyze form is submitted, show a loading state
  const uploadForm = document.getElementById("upload-form");
  if (uploadForm && submitBtn) {
    uploadForm.addEventListener("submit", () => {
      submitBtn.disabled = true;
      submitBtn.innerText = "Analyzing scan...";
    });
  }

  // ---------------- Animate probability bars on result page ----------------
  document.querySelectorAll(".prob-fill").forEach((bar) => {
    const target = bar.getAttribute("data-value") || "0";
    requestAnimationFrame(() => {
      bar.style.width = target + "%";
    });
  });

  // ---------------- Auto-dismiss flash messages ----------------
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => {
      flash.style.transition = "opacity 0.4s ease";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 400);
    }, 5000);
  });
});
