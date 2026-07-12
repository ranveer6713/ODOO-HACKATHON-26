"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import {
  Bell,
  Database,
  Monitor,
  Moon,
  Palette,
  RotateCcw,
  Server,
  Sun,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { localStore } from "@/lib/api/local-store";
import { API_BASE_URL } from "@/lib/api/client";
import { cn } from "@/lib/utils";

const PREF_KEY = "assetflow.prefs";

interface Prefs {
  emailNotifications: boolean;
  criticalAlerts: boolean;
  bookingReminders: boolean;
  maintenanceUpdates: boolean;
  weeklyDigest: boolean;
  density: "comfortable" | "compact";
}

const DEFAULT_PREFS: Prefs = {
  emailNotifications: true,
  criticalAlerts: true,
  bookingReminders: true,
  maintenanceUpdates: false,
  weeklyDigest: true,
  density: "comfortable",
};

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [prefs, setPrefs] = useState<Prefs>(DEFAULT_PREFS);
  const [resetOpen, setResetOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const raw = localStorage.getItem(PREF_KEY);
      if (raw) setPrefs({ ...DEFAULT_PREFS, ...JSON.parse(raw) });
    } catch {
      /* ignore */
    }
  }, []);

  function updatePref<K extends keyof Prefs>(key: K, value: Prefs[K]) {
    const next = { ...prefs, [key]: value };
    setPrefs(next);
    localStorage.setItem(PREF_KEY, JSON.stringify(next));
    toast.success("Preferences saved");
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Manage your workspace appearance, notifications and data." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Appearance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Palette className="size-4 text-muted-foreground" /> Appearance
              </CardTitle>
              <CardDescription>Customize how AssetFlow looks on your device.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <p className="mb-2 text-sm font-medium">Theme</p>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: "light", label: "Light", icon: Sun },
                    { value: "dark", label: "Dark", icon: Moon },
                    { value: "system", label: "System", icon: Monitor },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setTheme(opt.value)}
                      className={cn(
                        "flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors",
                        mounted && theme === opt.value
                          ? "border-primary bg-primary/5 text-primary"
                          : "hover:bg-muted/50",
                      )}
                    >
                      <opt.icon className="size-5" />
                      <span className="text-sm font-medium">{opt.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Bell className="size-4 text-muted-foreground" /> Notifications
              </CardTitle>
              <CardDescription>Choose which alerts you receive.</CardDescription>
            </CardHeader>
            <CardContent className="divide-y">
              <PrefRow
                label="Email notifications"
                description="Receive important updates by email."
                checked={prefs.emailNotifications}
                onChange={(v) => updatePref("emailNotifications", v)}
              />
              <PrefRow
                label="Critical alerts"
                description="Immediate alerts for critical events."
                checked={prefs.criticalAlerts}
                onChange={(v) => updatePref("criticalAlerts", v)}
              />
              <PrefRow
                label="Booking reminders"
                description="Reminders for upcoming returns and check-ins."
                checked={prefs.bookingReminders}
                onChange={(v) => updatePref("bookingReminders", v)}
              />
              <PrefRow
                label="Maintenance updates"
                description="Status changes on maintenance requests."
                checked={prefs.maintenanceUpdates}
                onChange={(v) => updatePref("maintenanceUpdates", v)}
              />
              <PrefRow
                label="Weekly digest"
                description="A weekly summary of estate activity."
                checked={prefs.weeklyDigest}
                onChange={(v) => updatePref("weeklyDigest", v)}
              />
            </CardContent>
          </Card>

          {/* Danger zone */}
          <Card className="border-destructive/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Database className="size-4 text-destructive" /> Local Data
              </CardTitle>
              <CardDescription>
                Assets, departments, employees and categories are stored in this browser for the demo.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                <div>
                  <p className="text-sm font-medium">Reset demo data</p>
                  <p className="text-sm text-muted-foreground">
                    Restore all local reference data to its original seed.
                  </p>
                </div>
                <Button variant="destructive" onClick={() => setResetOpen(true)}>
                  <RotateCcw className="size-4" /> Reset
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Connection */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Server className="size-4 text-muted-foreground" /> Connection
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">API base URL</p>
                <p className="mt-0.5 break-all font-mono text-xs">{API_BASE_URL}</p>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Version</span>
                <span className="font-medium">1.0.0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Environment</span>
                <span className="font-medium">Production</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Modules</span>
                <span className="font-medium">7 live</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <ConfirmDialog
        open={resetOpen}
        onOpenChange={setResetOpen}
        title="Reset demo data?"
        description="This restores all local assets, departments, employees and categories to their seed. This cannot be undone."
        confirmLabel="Reset data"
        destructive
        onConfirm={() => {
          localStore.reset();
          setResetOpen(false);
          toast.success("Demo data reset", { description: "Reload to see the fresh seed." });
          setTimeout(() => window.location.reload(), 800);
        }}
      />
    </div>
  );
}

function PrefRow({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-3.5">
      <div className="pr-4">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}
