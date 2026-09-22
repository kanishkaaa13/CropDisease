import { AlertCircle, BarChart3, CheckSquare, FileText, Layout, Map, MessageSquare, Scan, TrendingUp, Users, type LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const FARMER_NAV: NavItem[] = [
  { label: "My Farms", href: "/farmer", icon: Layout },
  { label: "Scan Leaf", href: "/farmer/scan", icon: Scan },
  { label: "Crop Prediction", href: "/predict", icon: TrendingUp },
  { label: "Alerts & Reports", href: "/farmer/reports", icon: AlertCircle },
  { label: "Government Schemes", href: "/farmer/schemes", icon: FileText },
  { label: "Chat with Officer", href: "/farmer/chat", icon: MessageSquare },
];

export const OFFICER_NAV: NavItem[] = [
  { label: "Overview", href: "/officer", icon: Layout },
  { label: "Validation Queue", href: "/officer/validations", icon: CheckSquare },
  { label: "Risk Map", href: "/officer/risk-map", icon: Map },
  { label: "Farmer Chats", href: "/officer/chats", icon: MessageSquare },
  { label: "Reports", href: "/officer/reports", icon: BarChart3 },
];

export const ADMIN_NAV: NavItem[] = [
  { label: "Overview", href: "/admin", icon: Layout },
  { label: "Analytics", href: "/admin/analytics", icon: BarChart3 },
  { label: "Hotspots", href: "/admin/hotspots", icon: Map },
  { label: "Users", href: "/admin/users", icon: Users },
];

export function getNavItems(role: string): NavItem[] {
  switch (role) {
    case "farmer":
      return FARMER_NAV;
    case "officer":
      return OFFICER_NAV;
    case "admin":
      return ADMIN_NAV;
    default:
      return [];
  }
}
