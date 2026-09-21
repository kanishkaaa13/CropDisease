export interface GovResource {
  title: string;
  description: string;
  url: string;
  icon: string;
}

export const GOV_RESOURCES: GovResource[] = [
  {
    title: "PM Fasal Bima Yojana (Crop Insurance)",
    description: "Apply for crop insurance and check claim status",
    url: "https://pmfby.gov.in/",
    icon: "🛡️",
  },
  {
    title: "Maharashtra Krishi Department",
    description: "State agriculture schemes, subsidies, and advisories",
    url: "https://krishi.maharashtra.gov.in/",
    icon: "🏛️",
  },
];
