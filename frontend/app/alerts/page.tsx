import {
  MarketStream,
} from "@/components/MarketStream";
import {
  PageShell,
} from "@/components/PageShell";
import {
  RiskAlerts,
} from "@/components/RiskAlerts";


export default function AlertsPage() {
  return (
    <PageShell
      title="Risk Alerts"
      description="Realtime market monitoring and deterministic risk alerts for the MVP."
    >
      <div className="space-y-8">
        <RiskAlerts
          symbol="AAPL"
        />

        <MarketStream
          symbol="AAPL"
        />
      </div>
    </PageShell>
  );
}
