import typing as t
from collections import defaultdict
from datetime import timedelta

from f1.handler import PacketHandler
from f1.packets import (
    SESSIONS,
    PacketFinalClassificationData,
    PacketLapData,
    PacketParticipantsData,
    PacketSessionData,
)

LapTime = t.Tuple[int, int]  # (lap number, lap time)


def fmtt(millis: int) -> str:
    return str(timedelta(milliseconds=millis))[2:-3]


def player_name(player) -> str:
    name = player.name.decode()
    return f"{name}{player.network_id}" if name == "Player" else name


class EvalRaceDataCollector(PacketHandler):
    def __init__(self, listener):
        super().__init__(listener)

        self.drivers: t.Dict[int, str] = {}
        self.laps: t.Dict[str, t.Set[LapTime]] = defaultdict(set)
        self.session_type = "<unknown>"
        self.link = None
        self.final_data: t.Dict[str, t.Any] = {}
        self.n_participants = 0

    def collect(self):
        return self.handle()

    # ---- PacketHandler ----

    def handle_SessionData(self, packet: PacketSessionData):
        if packet.session_link_identifier == self.link:
            return

        # New session
        self.session_type = SESSIONS[packet.session_type]
        self._session_type = self.session_type.lower().replace(" ", "_")

        print(self.session_type)

        self.link = packet.session_link_identifier

        self.laps = defaultdict(set)

    def handle_FinalClassificationData(self, packet: PacketFinalClassificationData):
        # get final position, best lap time and total race time
        final_names = set()
        for i, name in self.drivers.items():
            final_names.add(name)
            data = packet.classification_data[i]
            self.final_data[name] = {
                "position": data.position,
                "best_lap": data.best_lap_time_in_ms,
                "total_race_time": data.total_race_time,
                "penalties_time": data.penalties_time,
                "overall_time": data.penalties_time + data.total_race_time,
            }

        finished_drivers = sorted(
            (
                (name, data["position"], data["overall_time"])
                for name, data in self.final_data.items()
            ),
            key=lambda _: _[0],
        )

        # with open(f"{self.session_type.lower()}_laps.csv", "w") as laps_file:
        #     for name, ls in self.laps.items():
        #         laps = sorted(ls, key=lambda _: _[0])
        #         for n, t in laps:
        #             print(
        #                 f"{name},{n},{t},{fmtt(t)}",
        #                 file=laps_file,
        #             )

        with open(f"{self._session_type}_laps.csv", "w") as laps_file:
            # Header
            print(
                ",".join(("pos", "name", "lap", "time_ms", "time")),
                file=laps_file,
            )

            for name, p, _ in finished_drivers:
                laps = sorted(self.laps[name], key=lambda _: _[0])
                for n, t in laps:
                    print(
                        f"P{p},{name},{n},{t},{fmtt(t)}",
                        file=laps_file,
                    )

        with open(f"{self._session_type}_result.csv", "w") as final_file:
            # Header
            print(
                ",".join(("pos", "name", "best", "average", "sdev", "total", "pen")),
                file=final_file,
            )

            for name, p, _ in finished_drivers:
                result = self.final_data[name]
                times = (t for _, t in self.laps[name])
                avg = sum(times) / len(times)
                sdev = (
                    sum((t - avg) ** 2 for t in times) / len(times)
                ) ** 0.5 / 1000  # in seconds

                print(
                    ",".join(
                        (
                            f"P{p}",
                            name,
                            fmtt(result["best_lap"]),
                            fmtt(avg),
                            str(sdev),
                            fmtt(result["overall_time"]),
                            str(result["penalties_time"]),
                        )
                    ),
                    file=final_file,
                )

        # with open(f"{self.session_type.lower()}_result.csv", "w") as final_file:
        #     for name, result in sorted(
        #         self.final_data.items(), key=lambda _: _[1]["position"]
        #     ):
        #         print(
        #             f"P{result['position']},{name},{fmtt(result['best_lap'])}",
        #             file=final_file,
        #         )

        print(dict(self.laps))
        print(dict(self.final_data))

    def handle_LapData(self, packet: PacketLapData):
        # get last lap time for each car
        for i, name in self.drivers.items():
            data = packet.lap_data[i]
            if data.last_lap_time_in_ms:
                lap_time = (
                    data.current_lap_num - 1 + (data.result_status == 3),
                    data.last_lap_time_in_ms,
                )
                if lap_time not in self.laps[name]:
                    print(name, lap_time)
                    self.laps[name].add(lap_time)

    def handle_ParticipantsData(self, packet: PacketParticipantsData):
        self.drivers = {
            i: player_name(p)
            for i, p in enumerate(packet.participants)
            if p.name and not p.ai_controlled
        }

        n_participants = len(self.drivers)
        if self.n_participants != n_participants:
            print(n_participants, "participants", list(self.drivers.values()))
            self.n_participants = n_participants
