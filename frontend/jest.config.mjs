import nextJest from "next/jest.js";

// Load Next.js config so @/ path aliases match the app.
const createJestConfig = nextJest({ dir: "./" });

/** @type {import('jest').Config} */
const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  testMatch: [
    "<rootDir>/tests/unit/**/*.test.ts",
    "<rootDir>/tests/unit/**/*.test.tsx",
    "<rootDir>/tests/components/**/*.test.tsx",
    "<rootDir>/tests/integration/**/*.test.tsx",
  ],
  testPathIgnorePatterns: ["<rootDir>/tests/e2e/", "<rootDir>/node_modules/"],
  modulePathIgnorePatterns: ["<rootDir>/.next/"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^next/link$": "<rootDir>/tests/mocks/next-link.tsx",
    "^next/navigation$": "<rootDir>/tests/mocks/next-navigation.ts",
  },
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/app/**/layout.tsx",
    "!src/app/**/page.tsx",
  ],
};

export default createJestConfig(customJestConfig);
