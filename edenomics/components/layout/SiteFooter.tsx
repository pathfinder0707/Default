import { Container } from "@/components/layout/Section";
import { Wordmark } from "@/components/layout/Wordmark";

const COLUMNS = [
  { title: "Play", links: ["Today's run", "Skill map", "Portfolio lab", "League"] },
  { title: "About", links: ["How scoring works", "Our design rules", "Careers", "Press"] },
  { title: "Support", links: ["Help", "Contact", "Privacy", "Terms"] },
];

export function SiteFooter() {
  return (
    <footer className="border-line border-t pt-14 pb-28 lg:pb-14">
      <Container>
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <Wordmark />
            <p className="text-muted mt-4 max-w-xs text-[0.875rem] leading-relaxed">
              Finance is not hard. It is badly explained, and then priced as though it
              were hard.
            </p>
          </div>

          {COLUMNS.map((column) => (
            <div key={column.title} className="lg:col-span-2">
              <h3 className="label mb-4">{column.title}</h3>
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
            © {new Date().getFullYear()} Edenomics. Prototype — every price, company
            figure and rival on this page is illustrative sample data.
          </p>
          <p className="text-faint text-[0.75rem]">
            A learning game. Not investment advice, and nothing here is for sale.
          </p>
        </div>
      </Container>
    </footer>
  );
}
