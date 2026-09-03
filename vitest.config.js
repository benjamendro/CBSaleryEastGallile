import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['tests/js/**/*.test.js'],
    environment: 'jsdom',
    // The dashboard boots a large page and draws six figures; the default 5s is
    // tight for the first render on a cold runner.
    testTimeout: 30_000,
    hookTimeout: 60_000,
    // No coverage gate here on purpose: the dashboard's script ships inline in a
    // generated HTML file, so v8 cannot attribute it to a source file and any
    // threshold would be decoration. The pipeline's gate lives in pytest.ini
    // (--cov-fail-under), where it measures real modules.
  },
});
