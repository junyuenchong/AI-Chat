import type { ReactNode } from "react";

type LinkProps = {
  children: ReactNode;
  href: string;
};

/** Jest mock for next/link — renders a plain anchor in tests. */
export default function Link({ children, href }: LinkProps) {
  return <a href={href}>{children}</a>;
}
