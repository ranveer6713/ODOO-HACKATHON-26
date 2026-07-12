import {
  Activity,
  ArrowLeftRight,
  Bell,
  Boxes,
  CalendarClock,
  ClipboardCheck,
  FileBarChart,
  LayoutDashboard,
  Package,
  Settings,
  Tags,
  UserCog,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badgeKey?: "notifications";
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "Overview",
    items: [{ label: "Dashboard", href: "/dashboard", icon: LayoutDashboard }],
  },
  {
    title: "Organization",
    items: [
      { label: "Departments", href: "/departments", icon: Boxes },
      { label: "Employees", href: "/employees", icon: Users },
    ],
  },
  {
    title: "Assets",
    items: [
      { label: "Asset Categories", href: "/categories", icon: Tags },
      { label: "Assets", href: "/assets", icon: Package },
      { label: "Allocation", href: "/allocation", icon: UserCog },
      { label: "Transfers", href: "/transfers", icon: ArrowLeftRight },
    ],
  },
  {
    title: "Operations",
    items: [
      { label: "Resource Booking", href: "/booking", icon: CalendarClock },
      { label: "Maintenance", href: "/maintenance", icon: Wrench },
      { label: "Asset Audit", href: "/audit", icon: ClipboardCheck },
    ],
  },
  {
    title: "Insights",
    items: [
      { label: "Reports", href: "/reports", icon: FileBarChart },
      { label: "Activity Logs", href: "/activity", icon: Activity },
      { label: "Notifications", href: "/notifications", icon: Bell, badgeKey: "notifications" },
    ],
  },
  {
    title: "System",
    items: [{ label: "Settings", href: "/settings", icon: Settings }],
  },
];

/** Flat lookup for breadcrumbs / titles. */
export const NAV_LOOKUP: Record<string, string> = NAV_SECTIONS.flatMap(
  (s) => s.items,
).reduce(
  (acc, item) => {
    acc[item.href] = item.label;
    return acc;
  },
  {
    "/profile": "Profile",
    "/assets/[id]": "Asset Details",
  } as Record<string, string>,
);
