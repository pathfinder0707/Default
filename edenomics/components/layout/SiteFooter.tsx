import { Container } from "@/components/layout/Section";
import { Wordmark } from "@/components/layout/Wordmark";

const COLUMNS = [
  {
    title: "Product",
    links: ["Today's brief", "Markets", "Watchlist", "Daily challenge"],
  },
  {
    title: "Company",
    links: ["About", "Editorial standards", "Careers", "Press"],
  },
  {
    title: "Support",
    links: ["Help centre", "Contact", "Privacy", "Terms"],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-line border-t pt-14 pb-28 lg:pb-14">
      <Container>
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <Wordmark />
            <p className="text-muted mt-4 max-w-xs text-[0.875rem] leading-relaxed">
              Finance is not short of information. It is short of judgement about
              which information deserves your attention.
            </p>
          </div>

          {COLUMNS.map((column) => (
            <div key={column.title} className="lg:col-span-2">
              <h3 className="eyebrow mb-4">{column.title}</h3>
              <ul className="space-y-2.5">
                {column.links.map((link) => (
                  <li key={link}>
                    <span className="text-muted hover:text-fg cursor-default text-[0.875rem] transition-colors">
                      {link}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-line mt-12 flex flex-col gap-3 border-t pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-faint text-[0.75rem]">
            © {new Date().getFullYear()} Edenomics. Prototype — all prices, stories and
            figures on this page are illustrative sample data.
          </p>
          <p className="text-faint text-[0.75rem]">
            Nothing here is investment advice.
          </p>
        </div>
      </Container>
    </footer>
  );
}
