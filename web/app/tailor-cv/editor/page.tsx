"use client";

import { pdf } from "@react-pdf/renderer";
import Link from "next/link";
import { useEffect, useState } from "react";
import CVPDFDocument from "./CVPDFDocument";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type CVImprovement = {
  section: string;
  current_evidence: string;
  suggested_change: string;
  reason: string;
};

type CVImprovementItem = {
  section: string;
  field: string;
  reason: string;
  current_content: string;
  proposed_content: string;
  evidence_used: string[];
  expected_match_impact: string;
  safe_to_apply: boolean;
};

type CVImprovementPlan = {
  current_match: number;
  potential_match: number;
  overall_assessment: string;
  improvements: CVImprovementItem[];
  priority_order: string[];
  unsupported_requirements: string[];
  truth_warnings: string[];
  safe_to_apply_all: boolean;
};

type MatchingAnalysis = {
  match_percentage: number;
  overall_assessment: string;
  cv_improvements: CVImprovement[];
  suggested_rewrites: string[];
  tailoring_priority: string[];
};

type CVLink = {
  label: string;
  url: string;
};

type CVContact = {
  label: string;
  value: string;
  href?: string;
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

type TailorResult = {
  job_title: string | null;
  job_description: string;
  original_cv_text: string;
  job_analysis: Record<string, unknown>;
  cv_analysis: CVAnalysis;
  matching_analysis: MatchingAnalysis;
};

type SuggestionState = CVImprovement & {
  id: number;
  field: string;
  evidence_used: string[];
  expected_match_impact: string;
  safe_to_apply: boolean;
  status: "pending" | "applied" | "ignored";
};

function extractCVContacts(text: string): CVContact[] {
  const items: CVContact[] = [];

  const emails =
    text.match(
      /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi,
    ) || [];

  emails.forEach((email) => {
    if (
      !items.some(
        (item) => item.value.toLowerCase() === email.toLowerCase(),
      )
    ) {
      items.push({
        label: "Email",
        value: email,
        href: `mailto:${email}`,
      });
    }
  });

  const phones =
    text.match(/(?:\+?\d[\d\s().-]{7,}\d)/g) || [];

  phones.forEach((phone) => {
    const normalized = phone.replace(/\s+/g, " ").trim();

    if (
      normalized.replace(/\D/g, "").length >= 9 &&
      !items.some((item) => item.value === normalized)
    ) {
      items.push({
        label: "Phone",
        value: normalized,
        href: `tel:${normalized.replace(/[^\d+]/g, "")}`,
      });
    }
  });

  const urls =
    text.match(/https?:\/\/[^\s<>"')\]]+/gi) || [];

  urls.forEach((rawUrl) => {
    const url = rawUrl.replace(/[.,;:]+$/, "");
    const lower = url.toLowerCase();

    let label = "";

    if (lower.includes("linkedin.com")) {
      label = "LinkedIn";
    } else if (lower.includes("github.com")) {
      label = "GitHub";
    } else if (
      lower.includes("portfolio") ||
      lower.includes("vercel.app") ||
      lower.includes("netlify.app")
    ) {
      label = "Portfolio";
    }

    if (
      label &&
      !items.some((item) => item.href === url)
    ) {
      items.push({
        label,
        value: url.replace(/^https?:\/\//i, "").replace(/\/$/, ""),
        href: url,
      });
    }
  });

  return items;
}

function CVDocument({
  cv,
  originalCVText,
  contacts,
  onContactsChange,
  onChange,
}: {
  cv: CVAnalysis;
  originalCVText: string;
  contacts: CVContact[];
  onContactsChange: React.Dispatch<React.SetStateAction<CVContact[]>>;
  onChange: (cv: CVAnalysis) => void;
}) {
  function updateExperience(index: number, patch: Partial<CVExperience>) {
    const experiences = [...cv.experiences];
    experiences[index] = { ...experiences[index], ...patch };
    onChange({ ...cv, experiences });
  }

  function updateProject(index: number, patch: Partial<CVProject>) {
    const projects = [...cv.projects];
    projects[index] = { ...projects[index], ...patch };
    onChange({ ...cv, projects });
  }

  function updateArray(
    field:
      | "skills"
      | "education"
      | "certifications"
      | "tools_and_software"
      | "transferable_skills"
      | "industries"
      | "achievements",
    value: string,
  ) {
    onChange({
      ...cv,
      [field]: value
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean),
    });
  }

  function updateLink(
    links: CVLink[],
    index: number,
    patch: Partial<CVLink>,
  ) {
    return links.map((link, linkIndex) =>
      linkIndex === index ? { ...link, ...patch } : link,
    );
  }

  function addExperienceLink(index: number) {
    const experience = cv.experiences[index];
    updateExperience(index, {
      links: [...experience.links, { label: "Portfolio", url: "" }],
    });
  }

  function addProjectLink(index: number) {
    const project = cv.projects[index];
    updateProject(index, {
      links: [...project.links, { label: "Project", url: "" }],
    });
  }

  function removeExperienceLink(experienceIndex: number, linkIndex: number) {
    const experience = cv.experiences[experienceIndex];
    updateExperience(experienceIndex, {
      links: experience.links.filter((_, index) => index !== linkIndex),
    });
  }

  function removeProjectLink(projectIndex: number, linkIndex: number) {
    const project = cv.projects[projectIndex];
    updateProject(projectIndex, {
      links: project.links.filter((_, index) => index !== linkIndex),
    });
  }

  function EditableLine({
    value,
    onChange,
    placeholder,
    className = "",
  }: {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
  }) {
    return (
      <input
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className={`w-full rounded-sm border border-transparent bg-transparent px-1 py-0.5 outline-none transition hover:border-slate-200 focus:border-slate-300 focus:bg-slate-50 ${className}`}
      />
    );
  }

  function EditableText({
    value,
    onChange,
    placeholder,
    className = "",
    rows = 3,
  }: {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    rows?: number;
  }) {
    return (
      <textarea
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        className={`w-full resize-y rounded-sm border border-transparent bg-transparent px-1 py-1 outline-none transition hover:border-slate-200 focus:border-slate-300 focus:bg-slate-50 ${className}`}
      />
    );
  }

  function EditableBulletList({
    items,
    onChange,
    placeholder,
  }: {
    items: string[];
    onChange: (items: string[]) => void;
    placeholder: string;
  }) {
    return (
      <div className="space-y-1">
        {items.map((item, itemIndex) => (
          <div key={itemIndex} className="group flex items-start gap-2">
            <span className="mt-1.5 text-[10px] text-slate-500">●</span>

            <textarea
              value={item}
              onChange={(event) => {
                const updated = [...items];
                updated[itemIndex] = event.target.value;
                onChange(updated);
              }}
              rows={Math.max(1, Math.ceil(item.length / 105))}
              className="min-w-0 flex-1 resize-y rounded-sm border border-transparent bg-transparent px-1 py-0.5 text-[11.5px] leading-[1.55] text-slate-700 outline-none transition hover:border-slate-200 focus:border-slate-300 focus:bg-slate-50"
            />

            <button
              type="button"
              onClick={() =>
                onChange(items.filter((_, index) => index !== itemIndex))
              }
              className="mt-1 hidden text-xs text-slate-300 group-hover:block hover:text-red-500"
              aria-label="Remove bullet"
            >
              ×
            </button>
          </div>
        ))}

        <button
          type="button"
          onClick={() => onChange([...items, placeholder])}
          className="ml-5 mt-1 text-[10px] font-medium text-slate-400 hover:text-slate-800"
        >
          + Add bullet
        </button>
      </div>
    );
  }

  const editableContacts = contacts;

  function updateContact(
    index: number,
    patch: Partial<{ label: string; value: string; href?: string }>,
  ) {
    onContactsChange((contacts) =>
      contacts.map((contact, contactIndex) =>
        contactIndex === index
          ? { ...contact, ...patch }
          : contact,
      ),
    );
  }

  function removeContact(index: number) {
    onContactsChange((contacts) =>
      contacts.filter((_, contactIndex) => contactIndex !== index),
    );
  }

  function addContact() {
    onContactsChange((contacts) => [
      ...contacts,
      {
        label: "Contact",
        value: "",
        href: "",
      },
    ]);
  }

  const documentLinks = [
    ...cv.experiences.flatMap((experience) => experience.links),
    ...cv.projects.flatMap((project) => project.links),
  ].filter((link) => link.url);

  return (
    <div className="mx-auto w-full max-w-[794px] bg-slate-100 print:bg-white">
      <article className="min-h-[1123px] bg-white px-[42px] py-[40px] text-slate-900 shadow-[0_12px_40px_rgba(15,23,42,0.10)] print:min-h-0 print:max-w-none print:px-[38px] print:py-[34px] print:shadow-none">
        <header className="border-b-[3px] border-slate-900 pb-4">
          <EditableLine
            value={cv.candidate_name || ""}
            onChange={(value) => onChange({ ...cv, candidate_name: value })}
            placeholder="Your Name"
            className="text-[28px] font-bold leading-none tracking-[-0.035em]"
          />

          <EditableLine
            value={cv.likely_roles.join(" · ")}
            onChange={(value) =>
              onChange({
                ...cv,
                likely_roles: value
                  .split("·")
                  .map((item) => item.trim())
                  .filter(Boolean),
              })
            }
            placeholder="Professional title"
            className="mt-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-slate-600"
          />

          {editableContacts.length > 0 && (
            <div className="mt-3 grid grid-cols-2 gap-x-5 gap-y-1.5 text-[10px] text-slate-600 md:grid-cols-3">
              {editableContacts.map((item, index) => (
                <div
                  key={`${item.label}-${index}`}
                  className="group inline-flex items-center gap-1"
                >
                  <EditableLine
                    value={item.label}
                    onChange={(value) =>
                      updateContact(index, { label: value })
                    }
                    placeholder="Label"
                    className="font-semibold text-slate-500"
                  />

                  <span className="text-slate-300">·</span>

                  <EditableLine
                    value={item.value}
                    onChange={(value) => {
                      const trimmed = value.trim();
                      const label = item.label.toLowerCase();

                      let href = "";

                      if (label.includes("email")) {
                        href = trimmed ? `mailto:${trimmed}` : "";
                      } else if (label.includes("phone")) {
                        href = trimmed
                          ? `tel:${trimmed.replace(/[^\d+]/g, "")}`
                          : "";
                      } else if (
                        label.includes("linkedin") ||
                        label.includes("github") ||
                        label.includes("portfolio") ||
                        /^https?:\/\//i.test(trimmed)
                      ) {
                        href = trimmed
                          ? /^https?:\/\//i.test(trimmed)
                            ? trimmed
                            : `https://${trimmed}`
                          : "";
                      }

                      updateContact(index, {
                        value,
                        href,
                      });
                    }}
                    placeholder="Contact information"
                    className="text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-slate-950"
                  />

                  {item.href && (
                    <a
                      href={item.href}
                      target={item.href.startsWith("http") ? "_blank" : undefined}
                      rel={item.href.startsWith("http") ? "noreferrer" : undefined}
                      className="ml-0.5 text-[9px] text-slate-400 hover:text-slate-900"
                      title="Open link"
                    >
                      ↗
                    </a>
                  )}

                  <button
                    type="button"
                    onClick={() => removeContact(index)}
                    className="ml-0.5 hidden rounded px-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 group-hover:inline-flex"
                    title="Remove contact"
                  >
                    ×
                  </button>
                </div>
              ))}

              <button
                type="button"
                onClick={addContact}
                className="rounded border border-dashed border-slate-300 px-2 py-0.5 text-[9px] font-medium text-slate-500 hover:border-slate-400 hover:text-slate-700"
              >
                + Add contact
              </button>
            </div>
          )}
        </header>

        {cv.professional_summary && (
          <section className="mt-5">
            <SectionHeading title="Professional Summary" />
            <EditableText
              value={cv.professional_summary}
              onChange={(value) =>
                onChange({ ...cv, professional_summary: value })
              }
              placeholder="Write a concise professional summary..."
              rows={3}
              className="mt-2 text-[11.5px] leading-[1.6] text-slate-700"
            />
          </section>
        )}

        {cv.skills.length > 0 && (
          <section className="mt-5">
            <SectionHeading title="Core Skills" />
            <EditableText
              value={cv.skills.join("  •  ")}
              onChange={(value) =>
                updateArray(
                  "skills",
                  value.replace(/\s*•\s*/g, "\n"),
                )
              }
              placeholder="Add professional skills..."
              rows={3}
              className="mt-2 text-[11px] leading-[1.65] text-slate-700"
            />
          </section>
        )}

        {cv.experiences.length > 0 && (
          <section className="mt-5">
            <SectionHeading title="Professional Experience" />

            <div className="mt-3 space-y-5">
              {cv.experiences.map((experience, index) => (
                <article key={index}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <EditableLine
                        value={experience.role || ""}
                        onChange={(value) =>
                          updateExperience(index, { role: value })
                        }
                        placeholder="Job title"
                        className="text-[13px] font-bold"
                      />

                      <EditableLine
                        value={experience.organization || ""}
                        onChange={(value) =>
                          updateExperience(index, {
                            organization: value,
                          })
                        }
                        placeholder="Organization"
                        className="text-[11px] font-semibold text-slate-600"
                      />

                      {experience.location && (
                        <EditableLine
                          value={experience.location}
                          onChange={(value) =>
                            updateExperience(index, { location: value })
                          }
                          placeholder="Location"
                          className="text-[10px] text-slate-500"
                        />
                      )}
                    </div>

                    <div className="flex shrink-0 items-center gap-1 text-[10px] text-slate-500">
                      <EditableLine
                        value={experience.start_date || ""}
                        onChange={(value) =>
                          updateExperience(index, { start_date: value })
                        }
                        placeholder="Start"
                        className="w-[62px] text-right"
                      />
                      <span>–</span>
                      <EditableLine
                        value={experience.end_date || ""}
                        onChange={(value) =>
                          updateExperience(index, { end_date: value })
                        }
                        placeholder="Present"
                        className="w-[62px] text-right"
                      />
                    </div>
                  </div>

                  {(experience.responsibilities.length > 0 ||
                    experience.achievements.length > 0) && (
                    <div className="mt-2">
                      <EditableBulletList
                        items={[
                          ...experience.responsibilities,
                          ...experience.achievements,
                        ]}
                        onChange={(items) =>
                          updateExperience(index, {
                            responsibilities: items,
                            achievements: [],
                          })
                        }
                        placeholder="Describe an achievement or responsibility..."
                      />
                    </div>
                  )}

                  {experience.links.length > 0 && (
                    <div className="mt-2 space-y-1 border-l border-slate-200 pl-3">
                      {experience.links.map((link, linkIndex) => (
                        <div
                          key={linkIndex}
                          className="flex items-center gap-2"
                        >
                          <EditableLine
                            value={link.label}
                            onChange={(value) =>
                              updateExperience(index, {
                                links: updateLink(
                                  experience.links,
                                  linkIndex,
                                  { label: value },
                                ),
                              })
                            }
                            placeholder="Link label"
                            className="w-24 text-[9px] font-medium text-slate-500"
                          />

                          <EditableLine
                            value={link.url}
                            onChange={(value) =>
                              updateExperience(index, {
                                links: updateLink(
                                  experience.links,
                                  linkIndex,
                                  { url: value },
                                ),
                              })
                            }
                            placeholder="https://..."
                            className="text-[9px] text-slate-500"
                          />

                          <button
                            type="button"
                            onClick={() =>
                              removeExperienceLink(index, linkIndex)
                            }
                            className="text-[10px] text-slate-300 hover:text-red-500"
                            aria-label="Remove link"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => addExperienceLink(index)}
                    className="mt-1 text-[9px] font-medium text-slate-400 hover:text-slate-800"
                  >
                    + Add link
                  </button>
                </article>
              ))}
            </div>
          </section>
        )}

        {cv.projects.length > 0 && (
          <section className="mt-5">
            <SectionHeading title="Projects" />

            <div className="mt-3 space-y-4">
              {cv.projects.map((project, index) => (
                <article key={index}>
                  <EditableLine
                    value={project.name}
                    onChange={(value) =>
                      updateProject(index, { name: value })
                    }
                    placeholder="Project name"
                    className="text-[12.5px] font-bold"
                  />

                  <EditableText
                    value={project.description || ""}
                    onChange={(value) =>
                      updateProject(index, { description: value })
                    }
                    placeholder="Project description..."
                    rows={2}
                    className="mt-1 text-[11px] leading-[1.55] text-slate-700"
                  />

                  {project.technologies.length > 0 && (
                    <EditableText
                      value={project.technologies.join(", ")}
                      onChange={(value) =>
                        updateProject(index, {
                          technologies: value
                            .split(",")
                            .map((item) => item.trim())
                            .filter(Boolean),
                        })
                      }
                      placeholder="Skills, methods, technologies..."
                      rows={1}
                      className="mt-1 text-[10px] font-medium text-slate-500"
                    />
                  )}

                  {project.bullets.length > 0 && (
                    <div className="mt-1">
                      <EditableBulletList
                        items={project.bullets}
                        onChange={(bullets) =>
                          updateProject(index, { bullets })
                        }
                        placeholder="Describe the project..."
                      />
                    </div>
                  )}

                  {project.links.length > 0 && (
                    <div className="mt-2 space-y-1 border-l border-slate-200 pl-3">
                      {project.links.map((link, linkIndex) => (
                        <div
                          key={linkIndex}
                          className="flex items-center gap-2"
                        >
                          <EditableLine
                            value={link.label}
                            onChange={(value) =>
                              updateProject(index, {
                                links: updateLink(
                                  project.links,
                                  linkIndex,
                                  { label: value },
                                ),
                              })
                            }
                            placeholder="Link label"
                            className="w-24 text-[9px] font-medium text-slate-500"
                          />

                          <EditableLine
                            value={link.url}
                            onChange={(value) =>
                              updateProject(index, {
                                links: updateLink(
                                  project.links,
                                  linkIndex,
                                  { url: value },
                                ),
                              })
                            }
                            placeholder="https://..."
                            className="text-[9px] text-slate-500 underline decoration-slate-300 underline-offset-2"
                          />

                          {link.url && (
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[9px] text-slate-400 hover:text-slate-900"
                              title="Open link"
                            >
                              ↗
                            </a>
                          )}

                          <button
                            type="button"
                            onClick={() =>
                              removeProjectLink(index, linkIndex)
                            }
                            className="text-[10px] text-slate-300 hover:text-red-500"
                            aria-label="Remove link"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    onClick={() => addProjectLink(index)}
                    className="mt-1 text-[9px] font-medium text-slate-400 hover:text-slate-800"
                  >
                    + Add link
                  </button>
                </article>
              ))}
            </div>
          </section>
        )}

        {cv.education.length > 0 && (
          <section className="mt-5">
            <SectionHeading title="Education" />
            <EditableText
              value={cv.education.join("\n")}
              onChange={(value) => updateArray("education", value)}
              placeholder="Education"
              rows={Math.min(4, Math.max(2, cv.education.length))}
              className="mt-2 text-[11px] leading-[1.6]"
            />
          </section>
        )}

        {cv.certifications.length > 0 && (
          <section className="mt-5">
            <SectionHeading title="Certifications" />
            <EditableText
              value={cv.certifications.join("\n")}
              onChange={(value) => updateArray("certifications", value)}
              placeholder="Certifications"
              rows={Math.min(4, Math.max(2, cv.certifications.length))}
              className="mt-2 text-[11px] leading-[1.6]"
            />
          </section>
        )}

        {cv.achievements.length > 0 && (
          <section className="mt-5">
            <SectionHeading title="Achievements" />
            <EditableText
              value={cv.achievements.join("\n")}
              onChange={(value) => updateArray("achievements", value)}
              placeholder="Achievements"
              rows={Math.min(4, Math.max(2, cv.achievements.length))}
              className="mt-2 text-[11px] leading-[1.6]"
            />
          </section>
        )}
      </article>
    </div>
  );
}

function SectionHeading({ title }: { title: string }) {
  return (
    <h2 className="flex items-center gap-3 border-b border-slate-300 pb-1.5 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-900">
      <span>{title}</span>
      <span className="h-px flex-1 bg-slate-100" />
    </h2>
  );
}

export default function TailorCVEditorPage() {
  const [result, setResult] = useState<TailorResult | null>(null);
  const [cvText, setCVText] = useState("");
  const [cvAnalysis, setCVAnalysis] = useState<CVAnalysis | null>(null);
  const [editableContacts, setEditableContacts] = useState<CVContact[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionState[]>([]);
  const [improvementPlan, setImprovementPlan] =
    useState<CVImprovementPlan | null>(null);
  const [isImproving, setIsImproving] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get("session");
    const storageKey = sessionId
      ? `jobmatch_tailor_result:${sessionId}`
      : "jobmatch_tailor_result";
    const storedResult = sessionStorage.getItem(storageKey);

    queueMicrotask(() => {
      if (!storedResult) {
        setLoadError(
          "No CV analysis was found. Please return to the CV analysis page and run the analysis again.",
        );
        return;
      }

      try {
        const parsedResult = JSON.parse(storedResult) as TailorResult;

        const persistedCVAnalysis =
          (parsedResult as TailorResult & {
            cv_analysis?: CVAnalysis;
          }).cv_analysis ?? parsedResult.cv_analysis;

        const persistedCVText =
          (parsedResult as TailorResult & {
            cv_text?: string;
          }).cv_text ?? parsedResult.original_cv_text;

        const persistedContacts =
          (parsedResult as TailorResult & {
            editable_contacts?: CVContact[];
          }).editable_contacts ??
          extractCVContacts(parsedResult.original_cv_text);

        const persistedSuggestions =
          (parsedResult as TailorResult & {
            suggestions?: SuggestionState[];
          }).suggestions;

        const persistedImprovementPlan =
          (parsedResult as TailorResult & {
            improvement_plan?: CVImprovementPlan | null;
          }).improvement_plan;

        setResult(parsedResult);
        setCVText(persistedCVText);
        setCVAnalysis(persistedCVAnalysis);
        setEditableContacts(persistedContacts);

        if (persistedImprovementPlan) {
          setImprovementPlan(persistedImprovementPlan);
        }

        if (persistedSuggestions) {
          setSuggestions(persistedSuggestions);
          return;
        }

        setSuggestions(
          parsedResult.matching_analysis.cv_improvements.map(
            (improvement, index) => {
              const section = improvement.section.trim().toLowerCase();

              let field = "";

              if (
                section.includes("summary") ||
                section.includes("profile") ||
                section.includes("objective")
              ) {
                field = "professional_summary";
              } else if (section.includes("skill")) {
                field = "skills";
              } else if (section.includes("education")) {
                field = "education";
              } else if (section.includes("certification")) {
                field = "certifications";
              } else if (
                section.includes("tool") ||
                section.includes("software")
              ) {
                field = "tools_and_software";
              } else if (section.includes("transferable")) {
                field = "transferable_skills";
              } else if (section.includes("industry")) {
                field = "industries";
              } else if (section.includes("achievement")) {
                field = "achievements";
              } else if (
                section.includes("experience") ||
                section.includes("employment") ||
                section.includes("work history")
              ) {
                const experienceIndex = parsedResult.cv_analysis.experiences.findIndex(
                  (experience) =>
                    improvement.current_evidence.includes(
                      experience.role ?? "",
                    ) ||
                    improvement.current_evidence.includes(
                      experience.organization ?? "",
                    ),
                );

                if (experienceIndex >= 0) {
                  field = `experience.${experienceIndex}.responsibilities`;
                }
              } else if (section.includes("project")) {
                const projectIndex = parsedResult.cv_analysis.projects.findIndex(
                  (project) =>
                    improvement.current_evidence.includes(project.name),
                );

                if (projectIndex >= 0) {
                  field = `project.${projectIndex}.bullets`;
                }
              }

              return {
                ...improvement,
                id: index,
                field,
                evidence_used: [improvement.current_evidence],
                expected_match_impact: "Evidence-based improvement",
                safe_to_apply: Boolean(field),
                status: "pending",
              };
            },
          ),
        );
      } catch {
        setLoadError(
          "The saved CV analysis could not be loaded. Please run the analysis again.",
        );
      }
    });
  }, []);

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get("session");

    if (!sessionId || !result || !cvAnalysis) {
      return;
    }

    const storageKey = `jobmatch_tailor_result:${sessionId}`;
    const existing = sessionStorage.getItem(storageKey);

    if (!existing) {
      return;
    }

    try {
      const storedResult = JSON.parse(existing) as Record<string, unknown>;

      sessionStorage.setItem(
        storageKey,
        JSON.stringify({
          ...storedResult,
          ...result,
          cv_analysis: cvAnalysis,
          cv_text: cvText,
          editable_contacts: editableContacts,
          improvement_plan: improvementPlan,
          suggestions,
          updated_at: new Date().toISOString(),
        }),
      );
    } catch {
      // Keep the in-memory editor state if session persistence fails.
    }
  }, [
    result,
    cvAnalysis,
    cvText,
    editableContacts,
    improvementPlan,
    suggestions,
  ]);

  async function handleRecalculateMatch() {
    if (!result || !cvAnalysis) return;

    setIsReanalyzing(true);
    setSaveMessage("");

    try {
      const response = await fetch(`${API_URL}/api/cv/reanalyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_analysis: result.job_analysis,
          cv_analysis: cvAnalysis,
          original_cv_text: result.original_cv_text,
          job_description: result.job_description,
          job_title: result.job_title,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to recalculate the CV match.",
        );
      }

      const updatedResult: TailorResult = {
        ...result,
        matching_analysis: data.matching_analysis,
      };

      setResult(updatedResult);

      const sessionId = new URLSearchParams(
        window.location.search,
      ).get("session");

      if (sessionId) {
        sessionStorage.setItem(
          `jobmatch_tailor_result:${sessionId}`,
          JSON.stringify({
            ...updatedResult,
            cv_analysis: cvAnalysis,
            updated_at: new Date().toISOString(),
          }),
        );
      }

      setSaveMessage(
        `Match recalculated: ${data.matching_analysis.match_percentage}%.`,
      );
    } catch (error) {
      setSaveMessage(
        error instanceof Error
          ? error.message
          : "Unable to recalculate the CV match.",
      );
    } finally {
      setIsReanalyzing(false);
    }
  }

  async function handleImproveCV() {
    if (!result || !cvAnalysis) {
      return;
    }

    setIsImproving(true);
    setSaveMessage("");

    try {
      const response = await fetch(`${API_URL}/api/cv/improve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_analysis: result.job_analysis,
          cv_analysis: cvAnalysis,
          matching_analysis: result.matching_analysis,
          editable_cv_content: cvAnalysis,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to generate CV improvement suggestions.",
        );
      }

      const plan = data as CVImprovementPlan;

      setImprovementPlan(plan);

      setSuggestions(
        plan.improvements.map((improvement, index) => ({
          id: index,
          section: improvement.section,
          field: improvement.field,
          current_evidence: improvement.current_content,
          suggested_change: improvement.proposed_content,
          reason: improvement.reason,
          evidence_used: improvement.evidence_used,
          expected_match_impact: improvement.expected_match_impact,
          safe_to_apply: improvement.safe_to_apply,
          status: "pending",
        })),
      );

      setSaveMessage(
        `AI identified ${plan.improvements.length} evidence-based improvement(s).`,
      );
    } catch (error) {
      setSaveMessage(
        error instanceof Error
          ? error.message
          : "Unable to generate CV improvement suggestions.",
      );
    } finally {
      setIsImproving(false);
    }
  }

  function handleApplySuggestion(suggestion: SuggestionState) {
    setSaveMessage("");

    const proposedContent = suggestion.suggested_change.trim();

    if (!proposedContent || !cvAnalysis) {
      return;
    }

    const field = suggestion.field.trim().toLowerCase();

    const splitLines = (value: string) =>
      value
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean);

    const splitComma = (value: string) =>
      value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);

    const arrayFields = [
      "skills",
      "education",
      "certifications",
      "tools_and_software",
      "transferable_skills",
      "industries",
      "achievements",
      "likely_roles",
    ] as const;

    if (arrayFields.includes(field as (typeof arrayFields)[number])) {
      const key = field as (typeof arrayFields)[number];

      setCVAnalysis((currentCV) =>
        currentCV
          ? {
              ...currentCV,
              [key]: splitLines(proposedContent),
            }
          : currentCV,
      );

      setSuggestions((items) =>
        items.map((item) =>
          item.id === suggestion.id
            ? { ...item, status: "applied" }
            : item,
        ),
      );

      setSaveMessage(`Applied suggestion to ${suggestion.section}.`);
      return;
    }

    if (
      field === "professional_summary" ||
      field === "summary" ||
      field === "profile" ||
      field === "objective"
    ) {
      setCVAnalysis((currentCV) =>
        currentCV
          ? {
              ...currentCV,
              professional_summary: proposedContent,
            }
          : currentCV,
      );

      setSuggestions((items) =>
        items.map((item) =>
          item.id === suggestion.id
            ? { ...item, status: "applied" }
            : item,
        ),
      );

      setSaveMessage(`Applied suggestion to ${suggestion.section}.`);
      return;
    }

    const experienceMatch = field.match(
      /^(?:experience|experiences|employment|work)[._-]?(\d+)[._-](.+)$/,
    );

    const projectMatch = field.match(
      /^(?:project|projects)[._-]?(\d+)[._-](.+)$/,
    );

    if (experienceMatch) {
      const index = Number(experienceMatch[1]);
      const nestedField = experienceMatch[2];

      if (
        Number.isInteger(index) &&
        index >= 0 &&
        index < cvAnalysis.experiences.length
      ) {
        const allowedFields = [
          "role",
          "organization",
          "location",
          "start_date",
          "end_date",
          "responsibilities",
          "achievements",
          "industry",
        ];

        if (allowedFields.includes(nestedField)) {
          setCVAnalysis((currentCV) => {
            if (!currentCV) {
              return currentCV;
            }

            const experiences = [...currentCV.experiences];
            const experience = experiences[index];

            experiences[index] = {
              ...experience,
              [nestedField]:
                nestedField === "responsibilities" ||
                nestedField === "achievements"
                  ? splitLines(proposedContent)
                  : proposedContent,
            };

            return {
              ...currentCV,
              experiences,
            };
          });

          setSuggestions((items) =>
            items.map((item) =>
              item.id === suggestion.id
                ? { ...item, status: "applied" }
                : item,
            ),
          );

          setSaveMessage(`Applied suggestion to ${suggestion.section}.`);
          return;
        }
      }
    }

    if (projectMatch) {
      const index = Number(projectMatch[1]);
      const nestedField = projectMatch[2];

      if (
        Number.isInteger(index) &&
        index >= 0 &&
        index < cvAnalysis.projects.length
      ) {
        const allowedFields = [
          "name",
          "description",
          "technologies",
          "bullets",
        ];

        if (allowedFields.includes(nestedField)) {
          setCVAnalysis((currentCV) => {
            if (!currentCV) {
              return currentCV;
            }

            const projects = [...currentCV.projects];
            const project = projects[index];

            projects[index] = {
              ...project,
              [nestedField]:
                nestedField === "technologies"
                  ? splitComma(proposedContent)
                  : nestedField === "bullets"
                    ? splitLines(proposedContent)
                    : proposedContent,
            };

            return {
              ...currentCV,
              projects,
            };
          });

          setSuggestions((items) =>
            items.map((item) =>
              item.id === suggestion.id
                ? { ...item, status: "applied" }
                : item,
            ),
          );

          setSaveMessage(`Applied suggestion to ${suggestion.section}.`);
          return;
        }
      }
    }

    const evidence = suggestion.current_evidence.trim().toLowerCase();

    if (evidence) {
      const experienceIndex = cvAnalysis.experiences.findIndex(
        (experience) =>
          [
            experience.role,
            experience.organization,
            experience.location,
            ...experience.responsibilities,
            ...experience.achievements,
          ]
            .filter(Boolean)
            .some((value) =>
              value!.toLowerCase().includes(evidence),
            ),
      );

      if (experienceIndex >= 0) {
        setCVAnalysis((currentCV) => {
          if (!currentCV) {
            return currentCV;
          }

          const experiences = [...currentCV.experiences];
          const experience = experiences[experienceIndex];

          const responsibilityIndex =
            experience.responsibilities.findIndex((item) =>
              item.toLowerCase().includes(evidence),
            );

          if (responsibilityIndex >= 0) {
            const responsibilities = [...experience.responsibilities];
            responsibilities[responsibilityIndex] = proposedContent;

            experiences[experienceIndex] = {
              ...experience,
              responsibilities,
            };
          } else {
            const achievementIndex = experience.achievements.findIndex(
              (item) => item.toLowerCase().includes(evidence),
            );

            if (achievementIndex >= 0) {
              const achievements = [...experience.achievements];
              achievements[achievementIndex] = proposedContent;

              experiences[experienceIndex] = {
                ...experience,
                achievements,
              };
            } else if (
              experience.role?.toLowerCase().includes(evidence)
            ) {
              experiences[experienceIndex] = {
                ...experience,
                role: proposedContent,
              };
            } else if (
              experience.organization?.toLowerCase().includes(evidence)
            ) {
              experiences[experienceIndex] = {
                ...experience,
                organization: proposedContent,
              };
            }
          }

          return {
            ...currentCV,
            experiences,
          };
        });

        setSuggestions((items) =>
          items.map((item) =>
            item.id === suggestion.id
              ? { ...item, status: "applied" }
              : item,
          ),
        );

        setSaveMessage(`Applied suggestion to ${suggestion.section}.`);
        return;
      }

      const projectIndex = cvAnalysis.projects.findIndex(
        (project) =>
          [
            project.name,
            project.description,
            ...project.technologies,
            ...project.bullets,
          ]
            .filter(Boolean)
            .some((value) =>
              value!.toLowerCase().includes(evidence),
            ),
      );

      if (projectIndex >= 0) {
        setCVAnalysis((currentCV) => {
          if (!currentCV) {
            return currentCV;
          }

          const projects = [...currentCV.projects];
          const project = projects[projectIndex];

          const bulletIndex = project.bullets.findIndex((item) =>
            item.toLowerCase().includes(evidence),
          );

          if (bulletIndex >= 0) {
            const bullets = [...project.bullets];
            bullets[bulletIndex] = proposedContent;

            projects[projectIndex] = {
              ...project,
              bullets,
            };
          } else {
            projects[projectIndex] = {
              ...project,
              description: proposedContent,
            };
          }

          return {
            ...currentCV,
            projects,
          };
        });

        setSuggestions((items) =>
          items.map((item) =>
            item.id === suggestion.id
              ? { ...item, status: "applied" }
              : item,
          ),
        );

        setSaveMessage(`Applied suggestion to ${suggestion.section}.`);
        return;
      }
    }

    setSaveMessage(
      `The improvement for "${suggestion.section}" could not be mapped safely. Review and edit the CV manually.`,
    );
  }

  function handleIgnoreSuggestion(id: number) {
    setSaveMessage("");

    setSuggestions((currentSuggestions) =>
      currentSuggestions.map((item) =>
        item.id === id ? { ...item, status: "ignored" } : item,
      ),
    );
  }

  async function handleSaveAndGenerate() {
    if (!result || !cvAnalysis) {
      return;
    }

    setIsSaving(true);
    setSaveMessage("");

    try {
      const appliedSuggestions = suggestions
        .filter((suggestion) => suggestion.status === "applied")
        .map((suggestion) => ({
          section: suggestion.section,
          original: suggestion.current_evidence,
          change: suggestion.suggested_change,
        }));

      const ignoredSuggestions = suggestions
        .filter((suggestion) => suggestion.status === "ignored")
        .map((suggestion) => suggestion.section);

      sessionStorage.setItem(
        "jobmatch_tailored_cv",
        JSON.stringify({
          job_title: result.job_title,
          job_description: result.job_description,
          original_cv_text: result.original_cv_text,
          tailored_cv_text: cvText,
          tailored_cv_analysis: cvAnalysis,
          applied_suggestions: appliedSuggestions,
          ignored_suggestions: ignoredSuggestions,
          saved_at: new Date().toISOString(),
        }),
      );

      const blob = await pdf(
        <CVPDFDocument cv={cvAnalysis} contacts={editableContacts} />,
      ).toBlob();

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      const candidateName =
        cvAnalysis.candidate_name?.trim() || "JobMatch-CV";

      const safeName = candidateName
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-+|-+$/g, "");

      link.href = url;
      link.download = `${safeName || "JobMatch-CV"}-Tailored.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      URL.revokeObjectURL(url);

      setSaveMessage(
        "Your tailored CV has been saved and the new PDF has been generated.",
      );
    } catch (error) {
      setSaveMessage(
        error instanceof Error
          ? `Unable to generate PDF: ${error.message}`
          : "Unable to generate the tailored CV PDF.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (loadError) {
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
              CV Editor
            </span>
          </div>
        </header>

        <section className="px-6 py-12">
          <div className="mx-auto max-w-3xl">
            <Link
              href="/tailor-cv"
              className="text-sm font-medium text-slate-600 hover:text-slate-900"
            >
              ← Back to CV Analysis
            </Link>

            <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <h1 className="text-2xl font-bold">CV Editor</h1>

              <p className="mt-3 text-slate-600">{loadError}</p>

              <Link
                href="/tailor-cv"
                className="mt-6 inline-flex rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800"
              >
                Return to CV Analysis
              </Link>
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-900">
        <p className="text-sm text-slate-500">Loading your CV editor...</p>
      </main>
    );
  }

  const pendingSuggestions = suggestions.filter(
    (suggestion) => suggestion.status === "pending",
  );

  const appliedSuggestions = suggestions.filter(
    (suggestion) => suggestion.status === "applied",
  );

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
              J
            </div>

            <span className="text-xl font-bold tracking-tight">
              JobMatch
            </span>
          </Link>

          <span className="text-sm font-medium text-slate-500">
            CV Editor
          </span>
        </div>
      </header>

      <section className="px-6 py-10">
        <div className="mx-auto max-w-7xl">
          <Link
            href="/tailor-cv"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            ← Back to CV Analysis
          </Link>

          <div className="mt-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Tailor Your CV
            </p>

            <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">
                  {result.job_title || "Target Role"}
                </h1>

                <p className="mt-2 text-slate-600">
                  Review, apply, edit, or ignore evidence-based suggestions.
                </p>
              </div>

              <div className="flex flex-wrap items-stretch gap-3">
                <div className="rounded-2xl border border-slate-200 bg-white px-5 py-3 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Match
                  </p>

                  <p className="mt-1 text-2xl font-bold">
                    {result.matching_analysis.match_percentage}%
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleRecalculateMatch}
                  disabled={isReanalyzing || isImproving}
                  className="rounded-2xl border border-slate-300 bg-white px-5 py-3 text-left text-slate-900 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {isReanalyzing ? "Reanalyzing" : "Current CV"}
                  </span>
                  <span className="mt-1 block text-sm font-semibold">
                    {isReanalyzing
                      ? "Recalculating match..."
                      : "Recalculate Match ↻"}
                  </span>
                </button>

                <button
                  type="button"
                  onClick={handleImproveCV}
                  disabled={isImproving || isReanalyzing}
                  className="rounded-2xl border border-slate-900 bg-slate-900 px-5 py-3 text-left text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <span className="block text-xs font-semibold uppercase tracking-wide text-slate-300">
                    {isImproving ? "AI Working" : "Improve CV"}
                  </span>
                  <span className="mt-1 block text-sm font-semibold">
                    {isImproving
                      ? "Analyzing improvements..."
                      : "Improve for this job →"}
                  </span>
                </button>
              </div>
            </div>
          </div>

          {saveMessage && (
            <div className="mt-6 rounded-2xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-700 shadow-sm">
              {saveMessage}
            </div>
          )}

          <div className="mt-8 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <section
              id="cv-improvement-panel"
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                  AI Suggestions
                </p>

                <h2 className="mt-1 text-xl font-bold">
                  Review suggested improvements
                </h2>

                <p className="mt-2 text-sm text-slate-600">
                  Apply only changes you agree with. You remain in control of
                  every edit.
                </p>
              </div>

              {improvementPlan && (
                <div className="mt-6 space-y-4">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                        Current match
                      </p>
                      <p className="mt-1 text-2xl font-bold text-slate-900">
                        {improvementPlan.current_match}%
                      </p>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                        Potential match
                      </p>
                      <p className="mt-1 text-2xl font-bold text-slate-900">
                        {improvementPlan.potential_match}%
                      </p>
                    </div>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                        Safe to apply all
                      </p>
                      <p className="mt-1 text-sm font-bold text-slate-900">
                        {improvementPlan.safe_to_apply_all ? "Yes" : "Review first"}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      AI assessment
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {improvementPlan.overall_assessment}
                    </p>
                  </div>

                  {improvementPlan.unsupported_requirements.length > 0 && (
                    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
                        Unsupported requirements
                      </p>
                      <ul className="mt-2 space-y-1 text-sm leading-6 text-amber-900">
                        {improvementPlan.unsupported_requirements.map(
                          (requirement, index) => (
                            <li key={index}>• {requirement}</li>
                          ),
                        )}
                      </ul>
                    </div>
                  )}

                  {improvementPlan.truth_warnings.length > 0 && (
                    <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
                        Truth and accuracy warnings
                      </p>
                      <ul className="mt-2 space-y-1 text-sm leading-6 text-red-900">
                        {improvementPlan.truth_warnings.map(
                          (warning, index) => (
                            <li key={index}>• {warning}</li>
                          ),
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Improvement opportunity
                    </p>

                    <p className="mt-1 text-sm text-slate-700">
                      Your current CV matches this role at{" "}
                      <span className="font-bold text-slate-950">
                        {result.matching_analysis.match_percentage}%
                      </span>
                      .
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Review the evidence-based suggestions below and choose
                      which improvements you want to apply.
                    </p>
                  </div>

                  <div className="shrink-0 rounded-xl bg-white px-4 py-3 text-center shadow-sm">
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                      Suggestions
                    </p>
                    <p className="mt-1 text-xl font-bold text-slate-900">
                      {suggestions.filter(
                        (suggestion) => suggestion.status === "pending",
                      ).length}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                {suggestions.length === 0 ? (
                  <div className="rounded-2xl bg-slate-50 p-5">
                    <p className="font-semibold">
                      No specific CV improvements were suggested.
                    </p>
                  </div>
                ) : (
                  suggestions.map((suggestion) => (
                    <article
                      key={suggestion.id}
                      className={`rounded-2xl border p-5 ${
                        suggestion.status === "applied"
                          ? "border-slate-300 bg-slate-50"
                          : suggestion.status === "ignored"
                            ? "border-slate-200 bg-slate-50 opacity-60"
                            : "border-slate-200"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                            {suggestion.section}
                          </p>

                          <h3 className="mt-1 font-semibold">
                            Suggested improvement
                          </h3>
                        </div>

                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                          {suggestion.status === "applied"
                            ? "Applied"
                            : suggestion.status === "ignored"
                              ? "Ignored"
                              : "Review"}
                        </span>
                      </div>

                      <div className="mt-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Current evidence
                        </p>

                        <p className="mt-1 text-sm leading-6 text-slate-600">
                          {suggestion.current_evidence}
                        </p>
                      </div>

                      <div className="mt-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Proposed change
                        </p>

                        <p className="mt-1 rounded-xl bg-slate-50 p-3 text-sm leading-6 text-slate-800">
                          {suggestion.suggested_change}
                        </p>
                      </div>

                      <div className="mt-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                          Why
                        </p>

                        <p className="mt-1 text-sm leading-6 text-slate-600">
                          {suggestion.reason}
                        </p>
                      </div>

                      {suggestion.status === "pending" && (
                        <div className="mt-5 flex gap-3">
                          <button
                            type="button"
                            onClick={() => handleApplySuggestion(suggestion)}
                            className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
                          >
                            Apply
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleIgnoreSuggestion(suggestion.id)
                            }
                            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                          >
                            Ignore
                          </button>
                        </div>
                      )}
                    </article>
                  ))
                )}
              </div>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                  Your CV
                </p>

                <h2 className="mt-1 text-xl font-bold">
                  Edit your tailored CV
                </h2>

                <p className="mt-2 text-sm text-slate-600">
                  Your original CV is preserved. Changes here are made only to
                  the editable copy.
                </p>
              </div>

              {cvAnalysis ? (
                <div className="mt-6 overflow-auto rounded-2xl border border-slate-200 bg-slate-100 p-4">
                  <CVDocument
                    cv={cvAnalysis}
                    originalCVText={result.original_cv_text}
                    contacts={editableContacts}
                    onContactsChange={setEditableContacts}
                    onChange={(updatedCV) => {
                      setCVAnalysis(updatedCV);
                      setSaveMessage("");
                    }}
                  />
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
                  Structured CV data is unavailable. Please run the CV analysis
                  again.
                </div>
              )}

              <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-xs text-slate-500">
                  <p>{pendingSuggestions.length} suggestion(s) awaiting review.</p>
                  <p className="mt-1">
                    {appliedSuggestions.length} suggestion(s) applied.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleSaveAndGenerate}
                  disabled={isSaving}
                  className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSaving ? "Saving..." : "Save & Generate"}
                </button>
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}
