import type { ReactNode } from "react";

type PageShellProps = {
  title: string;
  description?: string;
  children?: ReactNode;
};

export function PageShell({
  title,
  description,
  children,
}: PageShellProps) {
  return (
    <main className="mx-auto min-h-[calc(100vh-4rem)] w-full max-w-6xl px-6 py-10">
      <section className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-950">
          {title}
        </h1>

        {description ? (
          <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600">
            {description}
          </p>
        ) : null}
      </section>

      {children}
    </main>
  );
}
