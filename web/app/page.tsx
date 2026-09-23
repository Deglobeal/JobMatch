"use client";

import { useState } from "react";

type Modal = "how-it-works" | "about" | null;

type Job = {
  title: string;
  company: string | null;
  location: string | null;
  employment_type: string | null;
  description: string | null;
  source: string;
  url: string;
};

type CVProfile = {
  filename: string;
  target_role: string | null;
  summary: string | null;
  skills: string[];
  experience: string | null;
  search_query: string;
};

type MatchRequirementDetail = {
  text: string;
  importance: string;
  status: string;
  category: string;
};

type MatchResult = {
  match_score: number;
  matched_requirements: string[];
  partial_matches: string[];
  missing_requirements: string[];
  requirement_details: MatchRequirementDetail[];
  keywords: string[];
  tailoring_suggestions: string[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [mode, setMode] = useState<"cv" | "job">("cv");
  const [modal, setModal] = useState<Modal>(null);
  const [searched, setSearched] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");

  const [jobs, setJobs] = useState<Job[]>([]);
  const [cvProfile, setCVProfile] = useState<CVProfile | null>(null);
  const [cvFile, setCVFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState("");
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);

  async function handleCVUpload(file: File) {
    setCVFile(file);
    setLoading(true);
    setError("");
    setCVProfile(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/api/cv/profile`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const message = await response.text();

        throw new Error(
          message || `CV processing failed with status ${response.status}`
        );
      }

      const data: CVProfile = await response.json();

      setCVProfile(data);
      setQuery(data.target_role || data.search_query || "");
    } catch (uploadError) {
      console.error(uploadError);

      setError(
        "Unable to process your CV right now. Make sure the JobMatch API is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleMatch() {
    if (!selectedJob || !cvProfile) {
      setMatchError("Upload your CV before analyzing this job.");
      return;
    }

    setMatching(true);
    setMatchError("");
    setMatchResult(null);

    try {
      const response = await fetch(`${API_URL}/api/jobs/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          cv_profile: cvProfile,
          job_title: selectedJob.title,
          job_description: selectedJob.description,
        }),
      });

      if (!response.ok) {
        const message = await response.text();

        throw new Error(
          message || `Match analysis failed with status ${response.status}`
        );
      }

      const data: MatchResult = await response.json();

      setMatchResult(data);
    } catch (matchErrorValue) {
      console.error(matchErrorValue);

      setMatchError(
        "Unable to analyze this job right now. Make sure the JobMatch API is running on port 8000."
      );
    } finally {
      setMatching(false);
    }
  }

  async function handleSearch() {
    if (!query.trim()) {
      setError(
        mode === "cv"
          ? "Upload your CV and confirm your target role first."
          : "Describe the job you are looking for first."
      );
      return;
    }

    setLoading(true);
    setError("");
    setSelectedJob(null);

    try {
      const response = await fetch(`${API_URL}/api/jobs/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
          location: location.trim() || null,
          employment_type: employmentType || null,
          experience_level: experienceLevel || null,
        }),
      });

      if (!response.ok) {
        const message = await response.text();

        throw new Error(
          message || `Search failed with status ${response.status}`
        );
      }

      const data = await response.json();

      setJobs(data.jobs || []);
      setSearched(true);
    } catch (searchError) {
      console.error(searchError);

      setError(
        "Unable to search for jobs right now. Make sure the JobMatch API is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  if (selectedJob) {
    return (
      <main className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
            <button
              onClick={() => setSelectedJob(null)}
              className="flex items-center gap-2"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
                J
              </div>

              <span className="text-xl font-bold tracking-tight">
                JobMatch
              </span>
            </button>
          </div>
        </header>

        <section className="px-6 py-12">
          <div className="mx-auto max-w-3xl">
            <button
              onClick={() => setSelectedJob(null)}
              className="mb-8 text-sm font-semibold text-slate-500 hover:text-slate-900"
            >
              ← Back to jobs
            </button>

            <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  {selectedJob.company || "Company not available"}
                </p>

                <h1 className="mt-2 text-3xl font-bold">
                  {selectedJob.title}
                </h1>

                <div className="mt-4 flex flex-wrap gap-2">
                  {selectedJob.location && (
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-sm">
                      {selectedJob.location}
                    </span>
                  )}

                  {selectedJob.employment_type && (
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-sm">
                      {selectedJob.employment_type}
                    </span>
                  )}

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-sm">
                    {selectedJob.source}
                  </span>
                </div>
              </div>

              <hr className="my-8 border-slate-200" />

              <h2 className="text-lg font-bold">Job description</h2>

              <div className="mt-4 rounded-2xl bg-slate-50 p-6">
                <p className="whitespace-pre-line text-sm leading-7 text-slate-600">
                  {selectedJob.description ||
                    "No job description was available from the source."}
                </p>
              </div>

              <div className="mt-8 rounded-2xl bg-slate-50 p-6">
                <h2 className="font-bold">What happens next?</h2>

                <p className="mt-2 text-sm leading-6 text-slate-600">
                  JobMatch will analyze this job against your CV, identify
                  important requirements, and help you prepare a tailored CV
                  and cover letter.
                </p>
              </div>

              {matchError && (
                <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
                  {matchError}
                </div>
              )}

              {matchResult && (
                <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-500">
                        Job match
                      </p>
                      <p className="mt-1 text-3xl font-bold">
                        {matchResult.match_score}%
                      </p>
                    </div>

                    <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
                      Requirements analyzed
                    </div>
                  </div>

                  <div className="mt-6">
                    <h3 className="font-bold">Matched requirements</h3>

                    {matchResult.matched_requirements.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {matchResult.matched_requirements.map((requirement) => (
                          <span
                            key={requirement}
                            className="rounded-full bg-emerald-50 px-3 py-1 text-sm text-emerald-700"
                          >
                            ✓ {requirement}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="mt-2 text-sm text-slate-500">
                        No direct requirements were matched.
                      </p>
                    )}
                  </div>

                  {matchResult.partial_matches.length > 0 && (
                    <div className="mt-6">
                      <h3 className="font-bold">Partial matches</h3>

                      <div className="mt-3 flex flex-wrap gap-2">
                        {matchResult.partial_matches.map((requirement) => (
                          <span
                            key={requirement}
                            className="rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-700"
                          >
                            ~ {requirement}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {matchResult.missing_requirements.length > 0 && (
                    <div className="mt-6">
                      <h3 className="font-bold">Potential gaps</h3>

                      <div className="mt-3 flex flex-wrap gap-2">
                        {matchResult.missing_requirements.map((requirement) => (
                          <span
                            key={requirement}
                            className="rounded-full bg-amber-50 px-3 py-1 text-sm text-amber-700"
                          >
                            • {requirement}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {matchResult.tailoring_suggestions.length > 0 && (
                    <div className="mt-6 rounded-xl bg-slate-50 p-4">
                      <h3 className="font-bold">Tailoring suggestions</h3>

                      <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-600">
                        {matchResult.tailoring_suggestions.map((suggestion) => (
                          <li key={suggestion}>• {suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={handleMatch}
                  disabled={matching || !cvProfile}
                  className="flex-1 rounded-xl bg-slate-900 px-6 py-4 font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {matching ? "Analyzing..." : "Analyze & Tailor CV"}
                </button>

                <a
                  href={selectedJob.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 rounded-xl border border-slate-300 px-6 py-4 text-center font-semibold hover:bg-slate-50"
                >
                  View Original Job
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
              J
            </div>

            <span className="text-xl font-bold tracking-tight">
              JobMatch
            </span>
          </div>

          <nav className="flex items-center gap-5 text-sm">
            <button
              onClick={() => setModal("how-it-works")}
              className="text-slate-600 hover:text-slate-900"
            >
              How it works
            </button>

            <button
              onClick={() => setModal("about")}
              className="text-slate-600 hover:text-slate-900"
            >
              About
            </button>
          </nav>
        </div>
      </header>

      {!searched ? (
        <section className="px-6 pb-20 pt-20 sm:pt-28">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-5 inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow-sm">
              Find jobs that actually match you
            </div>

            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Your next job starts with
              <span className="block text-slate-500">
                the right match.
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              Search jobs across the web using your CV or target role. Compare
              requirements, tailor your CV, generate a cover letter, and apply
              on the original job site.
            </p>
          </div>

          <div className="mx-auto mt-12 max-w-3xl rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/50 sm:p-8">
            <div className="mb-6 grid grid-cols-2 rounded-xl bg-slate-100 p-1">
              <button
                onClick={() => setMode("cv")}
                className={`rounded-lg px-4 py-3 text-sm font-semibold ${
                  mode === "cv"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Upload my CV
              </button>

              <button
                onClick={() => setMode("job")}
                className={`rounded-lg px-4 py-3 text-sm font-semibold ${
                  mode === "job"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Describe my target job
              </button>
            </div>

            {mode === "cv" ? (
              <div>
                {!cvProfile ? (
                  <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 px-6 py-12 text-center hover:bg-slate-50">
                    <div className="mb-3 text-3xl">↑</div>

                    <p className="font-semibold">
                      {loading
                        ? "Processing your CV..."
                        : "Drop your CV here"}
                    </p>

                    <p className="mt-1 text-sm text-slate-500">
                      PDF or DOCX, up to 10MB
                    </p>

                    <input
                      type="file"
                      accept=".pdf,.doc,.docx"
                      className="hidden"
                      disabled={loading}
                      onChange={(event) => {
                        const file = event.target.files?.[0];

                        if (file) {
                          handleCVUpload(file);
                        }
                      }}
                    />
                  </label>
                ) : (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-medium text-slate-500">
                          CV processed
                        </p>

                        <h3 className="mt-1 font-bold">
                          {cvFile?.name || cvProfile.filename}
                        </h3>
                      </div>

                      <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                        Ready
                      </span>
                    </div>

                    <div className="mt-6">
                      <label className="text-sm font-semibold">
                        Target role
                      </label>

                      <input
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-slate-500"
                      />
                    </div>

                    {cvProfile.skills.length > 0 && (
                      <div className="mt-5">
                        <p className="text-sm font-semibold">
                          Skills detected
                        </p>

                        <div className="mt-2 flex flex-wrap gap-2">
                          {cvProfile.skills.map((skill) => (
                            <span
                              key={skill}
                              className="rounded-lg bg-white px-3 py-1 text-xs font-medium text-slate-600"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Example: Junior Backend Developer using Python, FastAPI, PostgreSQL and REST APIs..."
                className="min-h-40 w-full resize-none rounded-2xl border border-slate-300 px-4 py-4 text-sm outline-none focus:border-slate-500"
              />
            )}

            <div className="mt-7">
              <p className="mb-3 text-sm font-semibold text-slate-700">
                Search preferences
              </p>

              <div className="grid gap-3 sm:grid-cols-3">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-slate-500">
                    Location
                  </label>
                  <input
                    value={location}
                    onChange={(event) => setLocation(event.target.value)}
                    placeholder="Remote / Nigeria"
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-500 focus:ring-2 focus:ring-slate-100"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-medium text-slate-500">
                    Employment
                  </label>
                  <select
                    value={employmentType}
                    onChange={(event) => setEmploymentType(event.target.value)}
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-100"
                  >
                    <option value="">Any type</option>
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                    <option value="Internship">Internship</option>
                  </select>
                </div>

                <div>
                  <label className="mb-1.5 block text-xs font-medium text-slate-500">
                    Experience
                  </label>
                  <select
                    value={experienceLevel}
                    onChange={(event) => setExperienceLevel(event.target.value)}
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-100"
                  >
                    <option value="">Any level</option>
                    <option value="Entry level">Entry level</option>
                    <option value="Junior">Junior</option>
                    <option value="Mid level">Mid level</option>
                    <option value="Senior">Senior</option>
                  </select>
                </div>
              </div>
            </div>

            {error && (
              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              onClick={handleSearch}
              disabled={loading}
              className="mt-6 w-full rounded-xl bg-slate-900 px-6 py-4 font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Searching the web..." : "Find Matching Jobs"}
            </button>
          </div>

          <div className="mx-auto mt-6 max-w-3xl">
            <a
              href="/tailor-cv"
              className="group flex flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="text-sm font-semibold text-slate-900">
                  Already have a job description?
                </p>

                <p className="mt-1 text-sm leading-6 text-slate-500">
                  Upload your CV and paste the job description to get a
                  detailed match analysis and CV improvement suggestions.
                </p>
              </div>

              <span className="inline-flex shrink-0 items-center justify-center rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition group-hover:bg-slate-700">
                Analyze a Job →
              </span>
            </a>
          </div>
        </section>
      ) : (
        <section className="px-6 py-12">
          <div className="mx-auto max-w-5xl">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div>
                <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">
                  Job results
                </p>

                <h1 className="mt-2 text-3xl font-bold">
                  Jobs matching your search
                </h1>

                <p className="mt-2 text-slate-600">
                  {jobs.length}{" "}
                  {jobs.length === 1
                    ? "opportunity"
                    : "opportunities"}{" "}
                  found
                </p>
              </div>

              <button
                onClick={() => {
                  setSearched(false);
                  setJobs([]);
                  setError("");
                }}
                className="rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold hover:bg-white"
              >
                New Search
              </button>
            </div>

            {jobs.length === 0 ? (
              <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                <h2 className="text-xl font-bold">
                  No matching jobs found
                </h2>

                <p className="mt-2 text-slate-600">
                  Try a broader job title, different location, or fewer
                  filters.
                </p>
              </div>
            ) : (
              <div className="mt-8 space-y-4">
                {jobs.map((job) => (
                  <article
                    key={`${job.url}-${job.title}`}
                    className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300 hover:shadow-md"
                  >
                    <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-500">
                          {job.company || "Company not available"}
                        </p>

                        <h2 className="mt-1 text-xl font-bold">
                          {job.title}
                        </h2>

                        <div className="mt-3 flex flex-wrap gap-2 text-sm text-slate-600">
                          {job.location && (
                            <span>{job.location}</span>
                          )}

                          {job.location &&
                            job.employment_type && (
                              <span>•</span>
                            )}

                          {job.employment_type && (
                            <span>{job.employment_type}</span>
                          )}
                        </div>

                        <div className="mt-4">
                          <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                            {job.source}
                          </span>
                        </div>
                      </div>

                      <div className="flex shrink-0 flex-col items-start gap-3 sm:items-end">
                        <button
                          onClick={() => setSelectedJob(job)}
                          className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700"
                        >
                          View Job
                        </button>
                      </div>
                    </div>

                    <div className="mt-5 border-t border-slate-100 pt-4 text-xs text-slate-400">
                      Source: {job.source}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {modal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-6 py-8 backdrop-blur-sm"
          onClick={() => setModal(null)}
        >
          <div
            className="relative max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-8 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              onClick={() => setModal(null)}
              className="absolute right-5 top-5 flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-xl"
            >
              ×
            </button>

            {modal === "how-it-works" ? (
              <>
                <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">
                  How it works
                </p>

                <h2 className="mt-3 text-3xl font-bold">
                  From your CV to your next application
                </h2>

                <div className="mt-8 space-y-6">
                  {[
                    ["01", "Tell JobMatch what you want"],
                    ["02", "Discover matching jobs"],
                    ["03", "Understand the match"],
                    ["04", "Tailor your application"],
                    ["05", "Apply on the original website"],
                    ["06", "Track your applications"],
                  ].map(([number, title]) => (
                    <div key={number} className="flex gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-xs font-bold text-white">
                        {number}
                      </div>

                      <div>
                        <h3 className="font-bold">{title}</h3>

                        <p className="mt-1 text-sm text-slate-600">
                          JobMatch helps you complete this stage while
                          keeping you in control of the final application.
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <p className="text-sm font-semibold uppercase tracking-widest text-slate-500">
                  About JobMatch
                </p>

                <h2 className="mt-3 text-3xl font-bold">
                  A smarter way to prepare for your job search
                </h2>

                <p className="mt-5 leading-7 text-slate-600">
                  JobMatch helps job seekers discover relevant
                  opportunities, understand how well they match a role,
                  and prepare stronger applications.
                </p>

                <div className="mt-8 rounded-2xl bg-slate-50 p-6">
                  <h3 className="font-bold">JobMatch helps you</h3>

                  <ul className="mt-4 space-y-3 text-sm text-slate-600">
                    <li>• Discover relevant jobs.</li>
                    <li>• Compare jobs with your CV.</li>
                    <li>• Identify matching and missing skills.</li>
                    <li>• Tailor your CV.</li>
                    <li>• Generate a cover letter.</li>
                    <li>• Track your applications.</li>
                  </ul>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

