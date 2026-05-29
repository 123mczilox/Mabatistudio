// Visualizer logic for roof preview, view switching, and details updates
const roofTypeButtons = document.querySelectorAll('[data-roof-type]');
const colorSwatches = document.querySelectorAll('[data-color]');
const viewButtons = document.querySelectorAll('[data-view]');
const roofImage = document.getElementById('roofImage');
const detailType = document.getElementById('detailType');
const detailGauge = document.getElementById('detailGauge');
const detailWarranty = document.getElementById('detailWarranty');
const detailPrice = document.getElementById('detailPrice');
const detailDescription = document.getElementById('detailDescription');

const imageBase = window.visualizerImageBase || '/static/images/';
const roofTypesElement = document.getElementById('roof-types-data');
const colorVariantsElement = document.getElementById('color-variants-data');
const roofTypes = roofTypesElement ? JSON.parse(roofTypesElement.textContent) : [];
const colorVariants = colorVariantsElement ? JSON.parse(colorVariantsElement.textContent) : [];

const roofData = {
  box: {
    label: 'Box Profile',
    gauge: '28 & 28',
    warranty: '15 year corrosion warranty',
    price: 'Ksh 180 - 260 / sqft',
    description: 'Clean lines and efficient water flow for a modern pitched roof.'
  },
  versatile: {
    label: 'Versatile',
    gauge: '28 & 30',
    warranty: '15 year performance warranty',
    price: 'Ksh 220 - 320 / sqft',
    description: 'A stylish profile with extra strength and premium roof coverage.'
  },
  corrugated: {
    label: 'Corrugated',
    gauge: '28 & 30',
    warranty: '15 year weather warranty',
    price: 'Ksh 160 - 240 / sqft',
    description: 'Affordable, durable and ideal for long-span roofing applications.'
  },
  stone: {
    label: 'Stone Coated',
    gauge: '26 only',
    warranty: '30 year premium warranty',
    price: 'Ksh 320 - 420 / sqft',
    description: 'Luxury finish with a modern architectural texture and depth.'
  }
};

let selectedType = roofTypes.length ? roofTypes[0].slug : 'box';
let selectedColor = colorVariants.length ? colorVariants[0].slug : 'red';
let activeView = 'front';

function updateRoofDetails() {
  const roof = roofData[selectedType] || {
    label: selectedType.replace(/-/g, ' '),
    gauge: 'Varies by profile',
    warranty: 'Contact us for warranty details',
    price: 'Contact for quote',
    description: 'Select a roof type and color to preview your configuration.',
  };
  detailType.textContent = roof.label;
  detailGauge.textContent = roof.gauge;
  detailWarranty.textContent = roof.warranty;
  detailPrice.textContent = roof.price;
  detailDescription.textContent = roof.description;
}

function updatePreviewImage() {
  // Build a list of candidate image paths (most specific → generic)
  const candidates = [];
  const variants = [
    `${activeView}-${selectedType}-${selectedColor}`,
    `${activeView}-${selectedType}`,
    `${selectedType}`,
    // older asset names used in the repo (examples)
    `${selectedType.replace('-', '_')}`,
  ];

  variants.forEach(v => {
    candidates.push(`${imageBase}${v}.jpg`);
    candidates.push(`${imageBase}${v}.png`);
    candidates.push(`${imageBase}${v}.svg`);
  });

  roofImage.style.opacity = '0';
  setTimeout(() => {
    // Try each candidate in order until one loads
    let i = 0;
    const tryNext = () => {
      if (i >= candidates.length) {
        // none found — reveal element so user sees broken image indicator
        roofImage.style.opacity = '1';
        return;
      }
      const src = candidates[i++];
      const tester = new Image();
      tester.onload = () => {
        roofImage.src = src;
        roofImage.style.opacity = '1';
      };
      tester.onerror = () => {
        tryNext();
      };
      tester.src = src;
    };
    tryNext();
  }, 120);
}

function setActiveButton(buttonGroup, value) {
  buttonGroup.forEach((btn) => {
    if (btn.dataset.roofType === value || btn.dataset.color === value || btn.dataset.view === value) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

roofTypeButtons.forEach((button) => {
  button.addEventListener('click', () => {
    selectedType = button.dataset.roofType;
    setActiveButton(roofTypeButtons, selectedType);
    updateRoofDetails();
    updatePreviewImage();
  });
});

colorSwatches.forEach((swatch) => {
  swatch.addEventListener('click', () => {
    selectedColor = swatch.dataset.color;
    setActiveButton(colorSwatches, selectedColor);
    updatePreviewImage();
  });
});

viewButtons.forEach((button) => {
  button.addEventListener('click', () => {
    activeView = button.dataset.view;
    setActiveButton(viewButtons, activeView);
    updatePreviewImage();
  });
});

// Initialize default selection once DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
  setActiveButton(roofTypeButtons, selectedType);
  setActiveButton(colorSwatches, selectedColor);
  setActiveButton(viewButtons, activeView);
  updateRoofDetails();
  updatePreviewImage();
});
