import ReactMarkdown from "react-markdown";
import type { Report } from "@/lib/types";

/** Renders the AI-generated strategy report (Markdown). */
export function ReportView({ report }: { report: Report | null }) {
  if (!report || !report.content_md) {
    return (
      <p className="text-sm text-slate-400">
        No report yet. It generates automatically after your channel is analyzed, or trigger
        one from the button above.
      </p>
    );
  }
  return (
    <article
      className="prose prose-sm prose-slate max-w-none dark:prose-invert
                 prose-headings:font-semibold prose-h1:text-lg prose-h2:text-base
                 prose-h2:mt-5 prose-p:text-slate-600 dark:prose-p:text-slate-300"
    >
      <ReactMarkdown>{report.content_md}</ReactMarkdown>
    </article>
  );
}
