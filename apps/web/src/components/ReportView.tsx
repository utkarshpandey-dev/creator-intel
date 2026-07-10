import ReactMarkdown from "react-markdown";
import { FileText } from "lucide-react";
import type { Report } from "@/lib/types";

/** Renders the AI-generated strategy report (Markdown) with editorial typography. */
export function ReportView({ report }: { report: Report | null }) {
  if (!report || !report.content_md) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-white/10 px-6 py-10 text-center">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/[0.05] text-slate-500">
          <FileText size={19} />
        </span>
        <p className="max-w-sm text-sm leading-relaxed text-slate-500">
          No report yet. One generates automatically after your channel is analyzed — or
          trigger one with the buttons above.
        </p>
      </div>
    );
  }
  return (
    <article
      className="prose prose-sm prose-invert max-w-none
                 prose-headings:font-display prose-headings:font-semibold prose-headings:text-white
                 prose-h1:text-lg prose-h2:mt-6 prose-h2:text-base
                 prose-p:leading-relaxed prose-p:text-slate-300
                 prose-strong:text-white prose-li:text-slate-300
                 prose-a:text-brand-300 prose-code:text-brand-200"
    >
      <ReactMarkdown>{report.content_md}</ReactMarkdown>
    </article>
  );
}
