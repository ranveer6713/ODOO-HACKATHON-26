"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  CalendarClock,
  ClipboardCheck,
  Mail,
  Phone,
  Shield,
  Wrench,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { Field } from "@/components/shared/form-field";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useSession } from "@/lib/auth/use-session";
import { setSession } from "@/lib/auth/session";
import { ROLE_LABELS } from "@/lib/auth/session";
import { useBookings } from "@/lib/hooks/use-bookings";
import { useMaintenanceList } from "@/lib/hooks/use-maintenance";
import { initials } from "@/lib/utils";

const schema = z.object({
  name: z.string().min(2, "Name is required"),
  email: z.string().email("Valid email required"),
  title: z.string().min(2, "Title is required"),
});
type FormValues = z.infer<typeof schema>;

export default function ProfilePage() {
  const { session } = useSession();

  const myBookings = useBookings({ requested_by: session?.id, page_size: 1 });
  const myMaintenance = useMaintenanceList({ page_size: 1 });

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    values: useMemo(
      () => ({
        name: session?.name ?? "",
        email: session?.email ?? "",
        title: session?.title ?? "",
      }),
      [session],
    ),
  });

  if (!session) return null;

  function onSubmit(values: FormValues) {
    setSession({ ...session!, name: values.name, email: values.email, title: values.title });
    reset(values);
    toast.success("Profile updated");
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Your account details and activity summary." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Identity card */}
        <Card className="lg:col-span-1">
          <CardContent className="flex flex-col items-center gap-4 p-6 text-center">
            <Avatar className="size-20 text-xl">
              <AvatarFallback>{initials(session.name)}</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-lg font-semibold">{session.name}</p>
              <p className="text-sm text-muted-foreground">{session.title}</p>
            </div>
            <StatusBadge tone="primary" label={ROLE_LABELS[session.role]} dot={false} />
            <div className="w-full space-y-2.5 border-t pt-4 text-left text-sm">
              <div className="flex items-center gap-2.5 text-muted-foreground">
                <Mail className="size-4" /> {session.email}
              </div>
              <div className="flex items-center gap-2.5 text-muted-foreground">
                <Shield className="size-4" /> {session.id}
              </div>
              <div className="flex items-center gap-2.5 text-muted-foreground">
                <Phone className="size-4" /> +1 415 555 0100
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Edit form + stats */}
        <div className="space-y-6 lg:col-span-2">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="My Bookings" value={myBookings.data?.meta.total ?? 0} icon={CalendarClock} tone="primary" />
            <StatCard label="Maintenance" value={myMaintenance.data?.meta.total ?? 0} icon={Wrench} tone="warning" />
            <StatCard label="Audits" value={0} icon={ClipboardCheck} tone="success" hint="Assigned to you" />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Account details</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <Field label="Full name" htmlFor="name" error={errors.name?.message} required>
                    <Input id="name" {...register("name")} />
                  </Field>
                  <Field label="Job title" htmlFor="title" error={errors.title?.message} required>
                    <Input id="title" {...register("title")} />
                  </Field>
                </div>
                <Field label="Email" htmlFor="email" error={errors.email?.message} required>
                  <Input id="email" type="email" {...register("email")} />
                </Field>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" disabled={!isDirty} onClick={() => reset()}>
                    Discard
                  </Button>
                  <Button type="submit" disabled={!isDirty}>
                    Save changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick links</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-2">
              <Button variant="outline" asChild className="justify-start">
                <Link href="/booking">
                  <CalendarClock className="size-4" /> My bookings
                </Link>
              </Button>
              <Button variant="outline" asChild className="justify-start">
                <Link href="/settings">
                  <Shield className="size-4" /> Settings
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
