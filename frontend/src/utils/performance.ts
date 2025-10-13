// Performance monitoring utilities for the enhanced dashboard

export const measurePerformance = (name: string, fn: () => void) => {
  const start = performance.now();
  fn();
  const end = performance.now();

  console.log(`${name} took ${end - start} milliseconds`);

  // Report to analytics if available
  if (window.gtag) {
    window.gtag("event", "timing_complete", {
      name: name,
      value: Math.round(end - start),
    });
  }
};

export const observeElementPerformance = (
  element: HTMLElement,
  callback: (entry: IntersectionObserverEntry) => void
) => {
  const observer = new IntersectionObserver(
    (entries: any) => {
      entries.forEach(callback);
    },
    {
      threshold: 0.1,
    }
  );

  observer.observe(element);

  return () => {
    observer.unobserve(element);
  };
};

export const preloadImages = (urls: string[]): Promise<void[]> => {
  return Promise.all(
    urls.map((url: any) => {
      return new Promise<void>((resolve: any) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => resolve(); // Still resolve to avoid blocking
        img.src = url;
      });
    })
  );
};
