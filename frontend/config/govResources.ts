import resourceData from "./government_resources.json";

export type ResourceCategory = "helpline" | "schemes" | string;
export type ResourceScope = "state" | "central";

export interface GovResource {
  id: string;
  category: ResourceCategory;
  nameKey: string;
  descriptionKey: string;
  scope: ResourceScope;
  url: string;
  phone?: string;
  status: string;
}

export const GOV_RESOURCES = resourceData.resources as GovResource[];
