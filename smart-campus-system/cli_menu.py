"""Interactive Menu-Driven CLI Simulation for Smart Campus Management (Case Study #100)."""

from campus_logic import MENU_OPTIONS, build_campus_summary, evaluate_attendance_record, process_event_registration, check_resource_allocation
from database import get_allocations, get_events, get_registrations, get_resources, get_students, init_db, register_student_event, allocate_resource


def run_cli_menu():
    """Run an interactive menu-driven campus management loop in the terminal."""
    init_db()
    while True:
        print("\n=== SMART CAMPUS MANAGEMENT SIMULATION (CASE STUDY #100) ===")
        for opt_num, opt_label in MENU_OPTIONS:
            print(f"  {opt_num}. {opt_label}")

        choice = input("Enter menu choice: ").strip()
        if choice == "0":
            print("Exiting Smart Campus Simulation. Goodbye!")
            break
        elif choice == "1":
            for st in get_students():
                print(f"  {st['student_id']} | {st['name']} | {st['department']} ({st['year']})")
        elif choice == "2":
            for st in get_students():
                ok, att, tot, pct, _ = evaluate_attendance_record(st["attended_classes"], st["total_classes"])
                flag = "SHORTAGE" if pct < 75.0 else "OK"
                if ok:
                    print(f"  {st['student_id']} | {st['name']}: {att}/{tot} ({pct}%) [{flag}]")
        elif choice == "3":
            summary = build_campus_summary(get_students(), get_events(), get_registrations(), get_resources(), get_allocations())
            for st in get_students():
                print(f"  {st['student_id']} | {st['name']}: Avg {st['avg_marks']}% (Grade {st['grade']})")
        elif choice == "4":
            sid = input("Student ID: ").strip().upper()
            ecode = input("Event Code (e.g. EVT101): ").strip().upper()
            ok, msg = process_event_registration(sid, ecode, get_events(), get_registrations())
            if ok:
                register_student_event(sid, ecode)
            print(" ", msg)
        elif choice == "5":
            rcode = input("Resource Code (e.g. RES-LAB1): ").strip().upper()
            req = input("Requester ID: ").strip().upper()
            slot = input("Slot (e.g. Fri 14:00-16:00): ").strip()
            ok, msg = check_resource_allocation(rcode, req, slot, get_resources(), get_allocations())
            if ok:
                allocate_resource(rcode, req, slot, "Campus Activity")
            print(" ", msg)
        elif choice == "6":
            summary = build_campus_summary(get_students(), get_events(), get_registrations(), get_resources(), get_allocations())
            print(summary["ascii_summary"])
        else:
            print("Invalid menu choice. Please select 0-6.")


if __name__ == "__main__":
    run_cli_menu()
