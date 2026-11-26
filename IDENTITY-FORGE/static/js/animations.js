document.addEventListener("DOMContentLoaded", function () {
  if (typeof gsap === "undefined") {
    return;
  }
  gsap.from(".panel", {
    y: 22,
    opacity: 0,
    duration: 0.65,
    stagger: 0.08,
    ease: "power2.out"
  });
  gsap.from(".metric-card", {
    y: 18,
    opacity: 0,
    duration: 0.55,
    stagger: 0.06,
    ease: "power2.out"
  });
});
