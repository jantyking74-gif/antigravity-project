// ============================================
// EduTrackX — Premium 3D Login Script
// Student Result Management System
// ============================================

(function () {
  'use strict';

  // ============================================
  // Loading Screen
  // ============================================
  window.addEventListener('load', () => {
    const loader = document.getElementById('loader-overlay');
    setTimeout(() => {
      loader.classList.add('fade-out');
      setTimeout(() => loader.remove(), 600);
    }, 1400);
  });

  // ============================================
  // Three.js Particle Background
  // ============================================
  function initParticleBackground() {
    if (typeof THREE === 'undefined') return;

    const canvas = document.getElementById('bg-canvas');
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 50;

    // Create particles
    const particleCount = 600;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const velocities = [];

    const colorPalette = [
      new THREE.Color(0x00c6ff), // cyan
      new THREE.Color(0x0072ff), // blue
      new THREE.Color(0x6432ff), // purple
      new THREE.Color(0x00ffc8), // mint
      new THREE.Color(0x4488ff), // light blue
    ];

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * 120;
      positions[i3 + 1] = (Math.random() - 0.5) * 120;
      positions[i3 + 2] = (Math.random() - 0.5) * 60;

      const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      colors[i3] = color.r;
      colors[i3 + 1] = color.g;
      colors[i3 + 2] = color.b;

      sizes[i] = Math.random() * 2.5 + 0.5;

      velocities.push({
        x: (Math.random() - 0.5) * 0.015,
        y: (Math.random() - 0.5) * 0.015,
        z: (Math.random() - 0.5) * 0.008,
      });
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // Custom shader for soft glowing dots
    const vertexShader = `
      attribute float size;
      varying vec3 vColor;
      void main() {
        vColor = color;
        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = size * (60.0 / -mvPosition.z);
        gl_Position = projectionMatrix * mvPosition;
      }
    `;

    const fragmentShader = `
      varying vec3 vColor;
      void main() {
        float dist = length(gl_PointCoord - vec2(0.5));
        if (dist > 0.5) discard;
        float alpha = 1.0 - smoothstep(0.1, 0.5, dist);
        gl_FragColor = vec4(vColor, alpha * 0.6);
      }
    `;

    const material = new THREE.ShaderMaterial({
      uniforms: {},
      vertexShader,
      fragmentShader,
      transparent: true,
      depthWrite: false,
      vertexColors: true,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Floating geometric shapes
    const shapeMaterial = new THREE.MeshBasicMaterial({
      color: 0x00c6ff,
      transparent: true,
      opacity: 0.04,
      wireframe: true,
    });

    const shapes = [];

    // Icosahedrons
    for (let i = 0; i < 5; i++) {
      const geo = new THREE.IcosahedronGeometry(
        Math.random() * 4 + 2,
        0
      );
      const mesh = new THREE.Mesh(geo, shapeMaterial.clone());
      mesh.material.opacity = Math.random() * 0.04 + 0.02;
      mesh.material.color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      mesh.position.set(
        (Math.random() - 0.5) * 80,
        (Math.random() - 0.5) * 80,
        (Math.random() - 0.5) * 30 - 10
      );
      mesh.userData = {
        rotSpeed: {
          x: (Math.random() - 0.5) * 0.004,
          y: (Math.random() - 0.5) * 0.004,
        },
        floatSpeed: Math.random() * 0.3 + 0.1,
        floatOffset: Math.random() * Math.PI * 2,
      };
      shapes.push(mesh);
      scene.add(mesh);
    }

    // Octahedrons
    for (let i = 0; i < 3; i++) {
      const geo = new THREE.OctahedronGeometry(Math.random() * 3 + 1.5);
      const mesh = new THREE.Mesh(geo, shapeMaterial.clone());
      mesh.material.opacity = Math.random() * 0.04 + 0.01;
      mesh.material.color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
      mesh.position.set(
        (Math.random() - 0.5) * 90,
        (Math.random() - 0.5) * 90,
        (Math.random() - 0.5) * 20 - 15
      );
      mesh.userData = {
        rotSpeed: {
          x: (Math.random() - 0.5) * 0.003,
          y: (Math.random() - 0.5) * 0.003,
        },
        floatSpeed: Math.random() * 0.2 + 0.1,
        floatOffset: Math.random() * Math.PI * 2,
      };
      shapes.push(mesh);
      scene.add(mesh);
    }

    // Mouse tracking for parallax
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    document.addEventListener('mousemove', (e) => {
      targetMouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      targetMouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    // Animation loop
    let time = 0;
    function animate() {
      requestAnimationFrame(animate);
      time += 0.01;

      // Smooth mouse follow
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Rotate particle field
      particles.rotation.y = mouseX * 0.08;
      particles.rotation.x = mouseY * 0.04;

      // Animate individual particles
      const pos = geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        pos[i3] += velocities[i].x;
        pos[i3 + 1] += velocities[i].y;
        pos[i3 + 2] += velocities[i].z;

        // Wrap around bounds
        if (Math.abs(pos[i3]) > 60) velocities[i].x *= -1;
        if (Math.abs(pos[i3 + 1]) > 60) velocities[i].y *= -1;
        if (Math.abs(pos[i3 + 2]) > 30) velocities[i].z *= -1;
      }
      geometry.attributes.position.needsUpdate = true;

      // Animate shapes
      shapes.forEach((shape) => {
        shape.rotation.x += shape.userData.rotSpeed.x;
        shape.rotation.y += shape.userData.rotSpeed.y;
        shape.position.y +=
          Math.sin(time * shape.userData.floatSpeed + shape.userData.floatOffset) * 0.03;
      });

      renderer.render(scene, camera);
    }

    animate();

    // Resize handler
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  // ============================================
  // 3D Card Tilt Effect
  // ============================================
  function initCardTilt() {
    const card = document.getElementById('login-card');
    const wrapper = document.getElementById('login-wrapper');
    if (!card || !wrapper) return;

    const maxTilt = 12;
    const maxShift = 8;

    wrapper.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const deltaX = (e.clientX - centerX) / (rect.width / 2);
      const deltaY = (e.clientY - centerY) / (rect.height / 2);

      const clampedX = Math.max(-1, Math.min(1, deltaX));
      const clampedY = Math.max(-1, Math.min(1, deltaY));

      const rotateY = clampedX * maxTilt;
      const rotateX = -clampedY * maxTilt;
      const shiftX = clampedX * maxShift;
      const shiftY = clampedY * maxShift;

      card.style.transform = `
        perspective(1000px)
        rotateX(${rotateX}deg)
        rotateY(${rotateY}deg)
        translateX(${shiftX}px)
        translateY(${shiftY}px)
        scale3d(1.02, 1.02, 1.02)
      `;
    });

    wrapper.addEventListener('mouseleave', () => {
      card.style.transition = 'transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
      card.style.transform =
        'perspective(1000px) rotateX(0deg) rotateY(0deg) translateX(0) translateY(0) scale3d(1,1,1)';
      setTimeout(() => {
        card.style.transition = 'transform 0.1s ease-out';
      }, 600);
    });

    // Make tilt smooth
    card.style.transition = 'transform 0.1s ease-out';
  }

  // ============================================
  // Parallax Floating Shapes
  // ============================================
  function initParallax() {
    const shapes = document.getElementById('floating-shapes');
    if (!shapes) return;

    document.addEventListener('mousemove', (e) => {
      const moveX = (e.clientX / window.innerWidth - 0.5) * 30;
      const moveY = (e.clientY / window.innerHeight - 0.5) * 30;

      shapes.style.transform = `translate(${moveX}px, ${moveY}px)`;
    });
  }

  // ============================================
  // Password Toggle
  // ============================================
  function initPasswordToggle() {
    const toggle = document.getElementById('eye-toggle');
    const password = document.getElementById('password-input');
    const eyeOpen = document.getElementById('eye-open');
    const eyeClosed = document.getElementById('eye-closed');

    if (!toggle || !password) return;

    toggle.addEventListener('click', () => {
      const isPassword = password.type === 'password';
      password.type = isPassword ? 'text' : 'password';
      eyeOpen.classList.toggle('hidden');
      eyeClosed.classList.toggle('hidden');
    });
  }

  // ============================================
  // Button Ripple Effect
  // ============================================
  function initRipple() {
    const btn = document.getElementById('sign-in-btn');
    if (!btn) return;

    btn.addEventListener('click', function (e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
      ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }

  // ============================================
  // Form Submission
  // ============================================
  function initFormSubmit() {
    const form = document.getElementById('login-form');
    const btn = document.getElementById('sign-in-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');

    if (!form || !btn) return;

    form.addEventListener('submit', (e) => {
      e.preventDefault();

      const enrollment = document.getElementById('enrollment-input').value.trim();
      const password = document.getElementById('password-input').value.trim();

      if (!enrollment || !password) {
        // Shake the card
        const card = document.getElementById('login-card');
        card.style.animation = 'none';
        card.offsetHeight; // reflow
        card.style.animation = 'shake 0.5s ease';
        setTimeout(() => (card.style.animation = ''), 500);

        // Highlight empty fields
        if (!enrollment) {
          highlightField('enrollment-group');
        }
        if (!password) {
          highlightField('password-group');
        }
        return;
      }

      // Loading state
      btn.disabled = true;
      btnText.classList.add('hidden');
      btnLoader.classList.remove('hidden');

      fetch('/api/student/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enrollment, password })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          btnText.classList.remove('hidden');
          btnLoader.classList.add('hidden');
          btnText.textContent = '✓ Welcome!';
          btn.style.animation = 'successPulse 0.6s ease';
          setTimeout(() => {
            window.location.href = '/student/dashboard';
          }, 1000);
        } else {
          btn.disabled = false;
          btnText.classList.remove('hidden');
          btnLoader.classList.add('hidden');
          
          const card = document.getElementById('login-card');
          card.style.animation = 'none';
          card.offsetHeight; // reflow
          card.style.animation = 'shake 0.5s ease';
          setTimeout(() => (card.style.animation = ''), 500);
          
          highlightField('enrollment-group');
          highlightField('password-group');
        }
      })
      .catch(err => {
        btn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        console.error('Login error:', err);
      });
    });
  }

  function highlightField(groupId) {
    const group = document.getElementById(groupId);
    if (!group) return;
    const input = group.querySelector('.form-input');
    input.style.borderColor = '#ff4466';
    input.style.boxShadow = '0 0 0 3px rgba(255, 68, 102, 0.15)';
    setTimeout(() => {
      input.style.borderColor = '';
      input.style.boxShadow = '';
    }, 1500);
  }

  // ============================================
  // Input Focus Sound Effect (Subtle)
  // ============================================
  function initInputAnimations() {
    const inputs = document.querySelectorAll('.form-input');
    inputs.forEach((input) => {
      input.addEventListener('focus', () => {
        const group = input.closest('.input-group');
        if (group) {
          group.style.transform = 'translateZ(25px) scale(1.02)';
          group.style.transition = 'transform 0.3s ease';
        }
      });

      input.addEventListener('blur', () => {
        const group = input.closest('.input-group');
        if (group) {
          group.style.transform = 'translateZ(15px) scale(1)';
        }
      });
    });
  }

  // ============================================
  // Initialize Everything
  // ============================================
  document.addEventListener('DOMContentLoaded', () => {
    initParticleBackground();
    initCardTilt();
    initParallax();
    initPasswordToggle();
    initRipple();
    initFormSubmit();
    initInputAnimations();
  });
})();
