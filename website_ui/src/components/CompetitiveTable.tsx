import { Check, X } from 'lucide-react';

interface RowData {
    feature: string;
    us: string;
    them: string;
}

interface CompetitiveTableProps {
    title: string;
    subtitle: string;
    competitorName: string;
    rows: RowData[];
}

export default function CompetitiveTable({ title, subtitle, competitorName, rows }: CompetitiveTableProps) {
    return (
        <section className="competitive-section">
            <div className="container">
                <div className="section-header text-center animate-fade-up">
                    <h2>{title}</h2>
                    <p className="subtitle" style={{ maxWidth: '600px', margin: '0 auto' }}>{subtitle}</p>
                </div>

                <div className="table-container animate-fade-up delay-1">
                    <table className="competitive-table">
                        <thead>
                            <tr>
                                <th className="feature-col">Capability</th>
                                <th className="us-col">JobsProof</th>
                                <th className="them-col">{competitorName}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((row, idx) => (
                                <tr key={idx}>
                                    <td className="feature-col">{row.feature}</td>
                                    <td className="us-col">
                                        <Check size={18} className="icon-success" />
                                        <span>{row.us}</span>
                                    </td>
                                    <td className="them-col">
                                        <X size={18} className="icon-fail" />
                                        <span>{row.them}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}
