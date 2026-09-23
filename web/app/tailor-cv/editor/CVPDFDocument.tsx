import {
  Document,
  Link as PDFLink,
  Page,
  StyleSheet,
  Text,
  View,
} from "@react-pdf/renderer";

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
  industries: string[];
  achievements: string[];
  evidence_notes: string[];
};

const styles = StyleSheet.create({
  page: {
    paddingTop: 34,
    paddingBottom: 34,
    paddingHorizontal: 44,
    fontFamily: "Helvetica",
    fontSize: 10,
    lineHeight: 1.28,
    color: "#1f2937",
  },
  header: {
    marginBottom: 11,
    borderBottomWidth: 1.5,
    borderBottomColor: "#111827",
    paddingBottom: 9,
  },
  contacts: {
    marginTop: 5,
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    alignItems: "center",
    columnGap: 10,
    rowGap: 2,
  },
  contact: {
    fontSize: 8,
    color: "#4b5563",
    textAlign: "center",
  },
  contactLabel: {
    fontFamily: "Helvetica-Bold",
    color: "#374151",
  },
  name: {
    fontSize: 20,
    fontFamily: "Helvetica-Bold",
    color: "#111827",
    marginBottom: 7,
  },
  subtitle: {
    fontSize: 9.5,
    color: "#4b5563",
    lineHeight: 1.4,
  },
  section: {
    marginTop: 9,
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 11.5,
    fontFamily: "Helvetica-Bold",
    textTransform: "uppercase",
    letterSpacing: 0.7,
    color: "#111827",
    borderBottomWidth: 0.7,
    borderBottomColor: "#d1d5db",
    paddingBottom: 2,
    marginBottom: 4,
  },
  summary: {
    fontSize: 10,
    color: "#374151",
  },
  item: {
    marginBottom: 6,
  },
  itemHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 8,
  },
  itemTitle: {
    flexGrow: 1,
    flexShrink: 1,
    fontSize: 9.5,
    fontFamily: "Helvetica-Bold",
    color: "#111827",
  },
  itemMeta: {
    flexShrink: 0,
    fontSize: 7.8,
    lineHeight: 1.2,
    color: "#6b7280",
    marginTop: 1,
  },
  organization: {
    fontSize: 8.5,
    color: "#4b5563",
    marginTop: 1,
  },
  bullet: {
    marginLeft: 9,
    marginTop: 1,
    fontSize: 8.8,
  },
  inlineList: {
    fontSize: 8.8,
    color: "#374151",
  },
  linkBlock: {
    marginTop: 2,
    paddingLeft: 8,
  },
  linkRow: {
    fontSize: 8,
    color: "#374151",
    marginBottom: 1,
  },
  linkLabel: {
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    color: "#374151",
  },
  linkUrl: {
    fontSize: 8,
    color: "#2563eb",
    textDecoration: "underline",
  },
  footer: {
    position: "absolute",
    bottom: 20,
    left: 46,
    right: 46,
    textAlign: "center",
    fontSize: 7.5,
    color: "#9ca3af",
  },
});

function BulletList({ items }: { items: string[] }) {
  return (
    <>
      {items.filter(Boolean).map((item, index) => (
        <Text key={`${item}-${index}`} style={styles.bullet}>
          • {item}
        </Text>
      ))}
    </>
  );
}

function Links({ links }: { links: CVLink[] }) {
  const validLinks = links.filter((link) => link.url?.trim());

  if (validLinks.length === 0) {
    return null;
  }

  return (
    <View style={styles.linkBlock}>
      {validLinks.map((link, index) => (
        <Text
          key={`${link.url}-${index}`}
          style={styles.linkRow}
        >
          <Text style={styles.linkLabel}>
            {link.label?.trim() || "Link"} |{" "}
          </Text>
          <PDFLink
            src={link.url.trim()}
            style={styles.linkUrl}
          >
            {link.url.trim()}
          </PDFLink>
        </Text>
      ))}
    </View>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

export default function CVPDFDocument({
  cv,
  contacts = [],
}: {
  cv: CVAnalysis;
  contacts?: CVContact[];
}) {
  const subtitle = cv.likely_roles
    .filter(Boolean)
    .join(" | ");

  return (
    <Document
      title={cv.candidate_name || "Tailored CV"}
      author="JobMatch"
      subject="Tailored CV"
    >
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.name}>
            {cv.candidate_name || "Professional CV"}
          </Text>

          {subtitle && (
            <Text style={styles.subtitle}>
              {subtitle}
            </Text>
          )}

          {contacts.length > 0 && (
            <View style={styles.contacts}>
              {contacts
                .filter((contact) => contact.value?.trim())
                .map((contact, index) => (
                  <View
                    key={`${contact.label}-${contact.value}-${index}`}
                    style={styles.contact}
                  >
                    <Text>
                      <Text style={styles.contactLabel}>
                        {contact.label?.trim() || "Contact"}
                      </Text>
                      {" | "}
                      {contact.href ? (
                        <PDFLink
                          src={contact.href}
                          style={styles.contact}
                        >
                          {contact.value.trim()}
                        </PDFLink>
                      ) : (
                        contact.value.trim()
                      )}
                    </Text>
                  </View>
                ))}
            </View>
          )}
        </View>

        {cv.professional_summary && (
          <Section title="Professional Summary">
            <Text style={styles.summary}>
              {cv.professional_summary}
            </Text>
          </Section>
        )}

        {cv.skills.length > 0 && (
          <Section title="Core Skills">
            <Text style={styles.inlineList}>
              {cv.skills.join(" • ")}
            </Text>
          </Section>
        )}

        {cv.experiences.length > 0 && (
          <Section title="Professional Experience">
            {cv.experiences.map((experience, index) => (
              <View
                key={`${experience.role}-${index}`}
                style={styles.item}
              >
                <View style={styles.itemHeader}>
                  <Text style={styles.itemTitle}>
                    {[
                      experience.role || "Experience",
                      experience.organization,
                      experience.location,
                    ]
                      .filter(Boolean)
                      .join(" | ")}
                  </Text>

                  <Text style={styles.itemMeta}>
                    {[experience.start_date, experience.end_date]
                      .filter(Boolean)
                      .join(" – ")}
                  </Text>
                </View>

                <BulletList
                  items={[
                    ...experience.responsibilities,
                    ...experience.achievements,
                  ]}
                />

                <Links links={experience.links} />
              </View>
            ))}
          </Section>
        )}

        {cv.projects.length > 0 && (
          <Section title="Projects">
            {cv.projects.map((project, index) => (
              <View
                key={`${project.name}-${index}`}
                style={styles.item}
              >
                <Text style={styles.itemTitle}>
                  {project.name}
                </Text>

                {project.technologies.length > 0 && (
                  <Text style={styles.itemMeta}>
                    {project.technologies.join(" • ")}
                  </Text>
                )}

                {project.description && (
                  <Text style={styles.summary}>
                    {project.description}
                  </Text>
                )}

                <BulletList items={project.bullets} />

                <Links links={project.links} />
              </View>
            ))}
          </Section>
        )}

        {cv.education.length > 0 && (
          <Section title="Education">
            <BulletList items={cv.education} />
          </Section>
        )}

        {cv.certifications.length > 0 && (
          <Section title="Certifications">
            <BulletList items={cv.certifications} />
          </Section>
        )}

        {cv.achievements.length > 0 && (
          <Section title="Achievements">
            <BulletList items={cv.achievements} />
          </Section>
        )}

        <Text
          style={styles.footer}
          render={({ pageNumber, totalPages }) =>
            `JobMatch • Page ${pageNumber} of ${totalPages}`
          }
          fixed
        />
      </Page>
    </Document>
  );
}
