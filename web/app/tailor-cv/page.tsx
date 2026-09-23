"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type MatchEvidence = {
  requirement: string;
  evidence: string;
  status: string;
};

type CVImprovement = {
  section: string;
  current_evidence: string;
  suggested_change: string;
  reason: string;
};

type MatchingAnalysis = {
  match_percentage: number;
  overall_assessment: string;
  strong_matches: MatchEvidence[];
  partial_matches: MatchEvidence[];
  missing_or_unclear: MatchEvidence[];
  transferable_experience: string[];
  keywords_to_consider: string[];
  cv_improvements: CVImprovement[];
  suggested_rewrites: string[];
  should_tailor_cv: boolean;
  tailoring_priority: string[];
  truth_warnings: string[];
};

type TruthCheckItem = {
  suggestion: string;
  status: string;
  evidence: string | null;
  reason: string;
};

type TruthCheckResult = {
  approved_suggestions: TruthCheckItem[];
  rejected_suggestions: TruthCheckItem[];
  warnings: string[];
  all_suggestions_safe: boolean;
};

type CVLink = {
  label: string;
  url: string;
};

type CVExperience = {
  role: string | null;
  organization: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  responsibilities: string[];
  achievements: string[];
  industry: string | null;
  links: CVLink[];
};

type CVProject = {
  name: string;
  description: string | null;
  technologies: string[];
  bullets: string[];
  links: CVLink[];
};

type CVAnalysis = {
  candidate_name: string | null;
  professional_summary: string | null;
  likely_roles: string[];
  seniority: string | null;
  skills: string[];
  experiences: CVExperience[];
  projects: CVProject[];
  education: string[];
  certifications: string[];
  tools_and_software: string[];
  industries: string[];
  transferable_skills: string[];
  achievements: string[];
  evidence_notes: string[];
};

type TailorResponse = {
  job_title: string | null;
  job_description: string;
  original_cv_text: string;
  cv_analysis: CVAnalysis;
  cv: {
    filename: string | null;
    target_role: string | null;
    summary: string | null;
    skills: string[];
    experience: unknown[];
    projects: unknown[];
    education: unknown[];
    certifications: unknown[];
    search_query: string | null;
  };
  matching_analysis: MatchingAnalysis;
  truth_check: TruthCheckResult;
};

export default function TailorCVPage() {
  const router = useRouter();
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [cvFile, setCVFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [result, setResult] = useState<TailorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] || null;

    setError("");
    setResult(null);

    if (!file) {
      setCVFile(null);
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(file.type)) {
      setCVFile(null);
      setError("Please upload your CV as a PDF or DOCX file.");
      return;
    }

    setCVFile(file);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!jobDescription.trim()) {
      setError("Please paste the job description.");
      return;
    }

    if (!cvFile) {
      setError("Please upload your CV as a PDF or DOCX file.");
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();

      formData.append("job_description", jobDescription.trim());

      if (jobTitle.trim()) {
        formData.append("job_title", jobTitle.trim());
      }

      formData.append("file", cvFile);

      const response = await fetch(
        `${API_URL}/api/cv/tailor`,
        {
          method: "POST",
          body: formData,
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Unable to analyze your CV right now.",
        );
      }

      setResult(data);

      const sessionId = crypto.randomUUID();
      sessionStorage.setItem(
        `jobmatch_tailor_result:${sessionId}`,
        JSON.stringify(data),
      );

      router.push(`/tailor-cv/editor?session=${sessionId}`);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to analyze your CV right now.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
              J
            </div>

            <span className="text-xl font-bold tracking-tight">
              JobMatch
            </span>
          </Link>

          <span className="text-sm font-medium text-slate-500">
            Tailor / Analyze CV
          </span>
        </div>
      </header>

      <section className="px-6 py-12">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              CV Analysis
            </p>

            <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
              Tailor / Analyze CV
            </h1>

            <p className="mt-3 text-slate-600">
              Paste a job description and upload your CV to see how well your
              experience matches the role.
            </p>
          </div>

          <form
            noValidate
            onSubmit={handleSubmit}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
          >
            <div className="space-y-6">
              <div>
                <label
                  htmlFor="job-title"
                  className="mb-2 block text-sm font-semibold"
                >
                  Job Title{" "}
                  <span className="font-normal text-slate-400">
                    (optional)
                  </span>
                </label>

                <input
                  id="job-title"
                  type="text"
                  value={jobTitle}
                  onChange={(event) => setJobTitle(event.target.value)}
                  placeholder="e.g. Junior Software Engineer"
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                />
              </div>

              <div>
                <label
                  htmlFor="job-description"
                  className="mb-2 block text-sm font-semibold"
                >
                  Job Description
                </label>

                <textarea
                  id="job-description"
                  value={jobDescription}
                  onChange={(event) => setJobDescription(event.target.value)}
                  placeholder="Paste the full job description here..."
                  rows={12}
                  className="w-full resize-y rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                />

                <p className="mt-2 text-xs text-slate-500">
                  Include the responsibilities, qualifications, skills, and
                  requirements from the original job posting.
                </p>
              </div>

              <div>
                <label
                  htmlFor="cv-upload"
                  className="mb-2 block text-sm font-semibold"
                >
                  Upload CV
                </label>

                <label
                  htmlFor="cv-upload"
                  className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 px-6 py-8 text-center transition hover:border-slate-400 hover:bg-slate-50"
                >
                  <span className="text-sm font-semibold">
                    {cvFile ? cvFile.name : "Choose your CV"}
                  </span>

                  <span className="mt-1 text-xs text-slate-500">
                    PDF or DOCX
                  </span>

                  <input
                    id="cv-upload"
                    type="file"
                    accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    onChange={handleFileChange}
                    className="sr-only"
                  />
                </label>

                {cvFile && (
                  <p className="mt-2 text-sm text-slate-600">
                    Selected:{" "}
                    <span className="font-medium">{cvFile.name}</span>
                  </p>
                )}
              </div>

              {error && (
                <div
                  role="alert"
                  className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                >
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full rounded-xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isLoading ? "Analyzing CV..." : "Analyze CV"}
              </button>
            </div>
          </form>

          {result && (
            <section className="mt-10 space-y-6">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                      Match Analysis
                    </p>

                    <h2 className="mt-2 text-2xl font-bold">
                      {result.job_title || "Target Role"}
                    </h2>

                    <p className="mt-2 max-w-2xl text-slate-600">
                      {result.matching_analysis.overall_assessment}
                    </p>
                  </div>

                  <div className="flex h-28 w-28 shrink-0 flex-col items-center justify-center rounded-full border-8 border-slate-200">
                    <span className="text-3xl font-bold">
                      {result.matching_analysis.match_percentage}%
                    </span>

                    <span className="text-xs text-slate-500">match</span>
                  </div>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                <AnalysisCard
                  title="Strong Matches"
                  items={result.matching_analysis.strong_matches}
                  type="strong"
                />

                <AnalysisCard
                  title="Partial Matches"
                  items={result.matching_analysis.partial_matches}
                  type="partial"
                />

                <AnalysisCard
                  title="Missing / Unclear"
                  items={result.matching_analysis.missing_or_unclear}
                  type="missing"
                />
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                <ListCard
                  title="Transferable Experience"
                  items={result.matching_analysis.transferable_experience}
                />

                <ListCard
                  title="Keywords to Consider"
                  items={result.matching_analysis.keywords_to_consider}
                />
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div className="mb-6">
                  <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    CV Improvements
                  </p>

                  <h2 className="mt-1 text-xl font-bold">
                    Evidence-based suggestions
                  </h2>
                </div>

                <div className="space-y-5">
                  {result.matching_analysis.cv_improvements.length > 0 ? (
                    result.matching_analysis.cv_improvements.map(
                      (improvement, index) => (
                        <div
                          key={`${improvement.section}-${index}`}
                          className="rounded-2xl border border-slate-200 p-5"
                        >
                          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                            <h3 className="font-semibold">
                              {improvement.section}
                            </h3>

                            <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                              Improvement {index + 1}
                            </span>
                          </div>

                          <div className="mt-4 grid gap-4 md:grid-cols-2">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Current evidence
                              </p>

                              <p className="mt-2 text-sm text-slate-600">
                                {improvement.current_evidence}
                              </p>
                            </div>

                            <div>
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Suggested change
                              </p>

                              <p className="mt-2 text-sm font-medium text-slate-900">
                                {improvement.suggested_change}
                              </p>
                            </div>
                          </div>

                          <p className="mt-4 text-sm text-slate-500">
                            <span className="font-semibold text-slate-700">
                              Why:
                            </span>{" "}
                            {improvement.reason}
                          </p>
                        </div>
                      ),
                    )
                  ) : (
                    <p className="text-sm text-slate-500">
                      No evidence-based CV improvements were identified.
                    </p>
                  )}
                </div>

                {result.matching_analysis.suggested_rewrites.length > 0 && (
                  <div className="mt-8">
                    <h3 className="font-semibold">Suggested rewrites</h3>

                    <ul className="mt-3 space-y-2">
                      {result.matching_analysis.suggested_rewrites.map(
                        (rewrite, index) => (
                          <li
                            key={index}
                            className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700"
                          >
                            {rewrite}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                      Truth Check
                    </p>

                    <h2 className="mt-1 text-xl font-bold">
                      Proposed changes verified against your original CV
                    </h2>
                  </div>

                  <span
                    className={`inline-flex w-fit rounded-full px-3 py-1.5 text-xs font-semibold ${
                      result.truth_check.all_suggestions_safe
                        ? "bg-green-100 text-green-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {result.truth_check.all_suggestions_safe
                      ? "All suggestions verified"
                      : "Review required"}
                  </span>
                </div>

                {result.truth_check.approved_suggestions.length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-semibold text-green-800">
                      Approved suggestions
                    </h3>

                    <div className="mt-3 space-y-3">
                      {result.truth_check.approved_suggestions.map(
                        (item, index) => (
                          <div
                            key={`approved-${index}`}
                            className="rounded-2xl border border-green-200 bg-green-50 p-4"
                          >
                            <p className="text-sm font-medium text-green-950">
                              {item.suggestion}
                            </p>

                            {item.evidence && (
                              <p className="mt-2 text-sm text-green-900">
                                <span className="font-semibold">
                                  Evidence:
                                </span>{" "}
                                {item.evidence}
                              </p>
                            )}

                            <p className="mt-2 text-xs text-green-800">
                              {item.reason}
                            </p>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {result.truth_check.rejected_suggestions.length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-semibold text-red-800">
                      Rejected suggestions
                    </h3>

                    <div className="mt-3 space-y-3">
                      {result.truth_check.rejected_suggestions.map(
                        (item, index) => (
                          <div
                            key={`rejected-${index}`}
                            className="rounded-2xl border border-red-200 bg-red-50 p-4"
                          >
                            <p className="text-sm font-medium text-red-950">
                              {item.suggestion}
                            </p>

                            {item.evidence && (
                              <p className="mt-2 text-sm text-red-900">
                                <span className="font-semibold">
                                  Evidence:
                                </span>{" "}
                                {item.evidence}
                              </p>
                            )}

                            <p className="mt-2 text-xs text-red-800">
                              {item.reason}
                            </p>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {result.truth_check.warnings.length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-semibold text-amber-800">
                      Truth-check warnings
                    </h3>

                    <ul className="mt-3 space-y-2">
                      {result.truth_check.warnings.map((warning, index) => (
                        <li
                          key={`truth-warning-${index}`}
                          className="text-sm text-amber-900"
                        >
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.truth_check.approved_suggestions.length === 0 &&
                  result.truth_check.rejected_suggestions.length === 0 &&
                  result.truth_check.warnings.length === 0 && (
                    <p className="mt-5 text-sm text-slate-500">
                      No concrete CV changes required verification.
                    </p>
                  )}
              </div>

              {result.matching_analysis.truth_warnings.length > 0 && (
                <div className="rounded-3xl border border-amber-200 bg-amber-50 p-6 sm:p-8">
                  <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">
                    Truth & Evidence Warnings
                  </p>

                  <ul className="mt-3 space-y-2">
                    {result.matching_analysis.truth_warnings.map(
                      (warning, index) => (
                        <li
                          key={index}
                          className="text-sm text-amber-900"
                        >
                          {warning}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              )}

              {result.matching_analysis.should_tailor_cv && (
                <div className="rounded-3xl border border-slate-200 bg-slate-900 p-6 text-white shadow-sm sm:p-8">
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-wide text-slate-300">
                        Ready for the next step?
                      </p>

                      <h2 className="mt-1 text-xl font-bold">
                        Tailor your CV using these suggestions
                      </h2>

                      <p className="mt-2 max-w-2xl text-sm text-slate-300">
                        The original CV will remain unchanged. You will review
                        proposed edits before anything is applied.
                      </p>
                    </div>

                    <Link
                      href="/tailor-cv/editor"
                      className="shrink-0 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
                    >
                      Tailor My CV
                    </Link>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      </section>
    </main>
  );
}

function AnalysisCard({
  title,
  items,
  type,
}: {
  title: string;
  items: MatchEvidence[];
  type: "strong" | "partial" | "missing";
}) {
  const icon = type === "strong" ? "✓" : type === "partial" ? "◐" : "✕";

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold">{title}</h2>

      {items.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">None identified.</p>
      ) : (
        <div className="mt-4 space-y-4">
          {items.map((item, index) => (
            <div key={`${item.requirement}-${index}`}>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-sm font-bold">{icon}</span>

                <div>
                  <p className="text-sm font-semibold">
                    {item.requirement}
                  </p>

                  <p className="mt-1 text-sm text-slate-600">
                    {item.evidence}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ListCard({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold">{title}</h2>

      {items.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">None identified.</p>
      ) : (
        <ul className="mt-4 flex flex-wrap gap-2">
          {items.map((item, index) => (
            <li
              key={`${item}-${index}`}
              className="rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-700"
            >
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
