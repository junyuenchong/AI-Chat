/** Jest mock for next/navigation — no-op router in unit tests. */
export const useRouter = () => ({
  push: jest.fn(),
  replace: jest.fn(),
  refresh: jest.fn(),
  back: jest.fn(),
});

export const usePathname = () => "/chat";
