import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: '"Inter", sans-serif',
});

export default function Mermaid({ chart }: { chart: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');

    useEffect(() => {
        const renderChart = async () => {
            if (chart) {
                try {
                    // Generate random id to avoid DOM conflicts
                    const id = `mermaid-${Math.round(Math.random() * 100000)}`;
                    const { svg } = await mermaid.render(id, chart);
                    setSvg(svg);
                } catch (e) {
                    console.error("Mermaid rendering error:", e);
                }
            }
        };
        renderChart();
    }, [chart]);

    return (
        <div
            className="mermaid-wrapper"
            ref={containerRef}
            dangerouslySetInnerHTML={{ __html: svg }}
            style={{ display: 'flex', justifyContent: 'center', width: '100%' }}
        />
    );
}
