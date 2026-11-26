export type Mission = {
  id_mission: string;
  title: string;
  start_at?: string | null;
  finish_at?: string | null;
  seat_number?: number | null;
  required_skills: string[];
  status: string;
  id_collect?: string | null;
  id_event?: string | null;
  place?: string | null;
  remaining_seats?: number | null;
};
