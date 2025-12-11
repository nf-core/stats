---
title: Modules Updates
sidebar_position: 9
---

# nf-core/modules Update Tracking

This page tracks the adoption of various module metadata and configuration updates across the nf-core/modules repository.

```sql modules_stats
select
    timestamp,
    total_modules,
    modules_converted,
    modules_with_old_pattern,
    modules_with_topics_version,
    modules_without_topics_version,
    modules_with_wave_containers,
    modules_without_wave_containers,
    -- Percentage calculations
    modules_converted / nullif(total_modules, 0)::float as modules_converted_pct,
    modules_with_old_pattern / nullif(total_modules, 0)::float as modules_with_old_pattern_pct,
    modules_with_topics_version / nullif(total_modules, 0)::float as modules_with_topics_version_pct,
    modules_without_topics_version / nullif(total_modules, 0)::float as modules_without_topics_version_pct,
    modules_with_wave_containers / nullif(total_modules, 0)::float as modules_with_wave_containers_pct,
    modules_without_wave_containers / nullif(total_modules, 0)::float as modules_without_wave_containers_pct
from nfcore_db.modules_container_conversion
order by timestamp desc
```

## Current Status

<BigValue
    data={modules_stats}
    value=total_modules
    title="Total number of modules"
    sparkline=timestamp
    />
<BigValue
    data={modules_stats}
    value=modules_converted
    title="New Container Syntax"
    sparkline=timestamp
    />

<BigValue
    data={modules_stats}
    value=modules_with_topics_version
    title="Modules with Version Topics"
    sparkline=timestamp
    />

<BigValue
    data={modules_stats}
    value=modules_with_wave_containers
    title="Modules with Wave containers"
    sparkline=timestamp
    />

## New Container Syntax Adoption Over Time

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={modules_stats}
            x=timestamp
            y={['modules_converted_pct', 'modules_with_old_pattern_pct']}
            title="New Container Syntax Adoption Timeline (%)"
            yFmt="pct0"
            yMax={1}
        />
    </Tab>
    <Tab label="Total Numbers">
        <AreaChart
            data={modules_stats}
            x=timestamp
            y={['modules_converted', 'modules_with_old_pattern']}
            title="New Container Syntax Adoption Timeline"
            yAxisTitle="Number of Modules"
        />
    </Tab>
</Tabs>

## Version Topics Adoption Over Time

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={modules_stats}
            x=timestamp
            y={['modules_with_topics_version_pct', 'modules_without_topics_version_pct']}
            title="Version Topics Adoption Timeline (%)"
            yFmt="pct0"
            xFmt="m/d"
            yMax={1}
        />
    </Tab>
    <Tab label="Total Numbers">
        <AreaChart
            data={modules_stats}
            x=timestamp
            y={['modules_with_topics_version', 'modules_without_topics_version']}
            title="Version Topics Adoption Timeline"
            yAxisTitle="Number of Modules"
        />
    </Tab>
</Tabs>

## Wave Containers Adoption Over Time

<Tabs>
    <Tab label="Percentage">
        <AreaChart
            data={modules_stats}
            x=timestamp
            y={['modules_with_wave_containers_pct', 'modules_without_wave_containers_pct']}
            title="Wave Containers Adoption Timeline (%)"
            yFmt="pct0"
            yMax={1}
        />
    </Tab>
    <Tab label="Total Numbers">
        <AreaChart
            data={modules_stats}
            x=timestamp
            y={['modules_with_wave_containers', 'modules_without_wave_containers']}
            title="Wave Containers Adoption Timeline"
            yAxisTitle="Number of Modules"
        />
    </Tab>
</Tabs>

## Details

This page tracks several module update metrics for nf-core modules:

1. **New Container Syntax**: Modules that have adopted the new container syntax (measured by the presence of `linux_amd64` in their `meta.yml` files)
2. **Version Topics**: Modules that have converted to using version topics (measured by the presence of `topics: versions:` in their `meta.yml` files)
3. **Wave Containers**: Modules that use `community.wave.seqera.io/library/` containers in their `main.nf` files

These metrics help track the adoption of best practices and standardization efforts across the nf-core modules repository.

```sql modules_history
select
    timestamp,
    total_modules,
    modules_with_old_pattern,
    modules_converted,
    modules_with_topics_version,
    modules_without_topics_version,
    modules_with_wave_containers,
    modules_without_wave_containers,
from nfcore_db.modules_container_conversion
order by timestamp desc
```

<DataTable
data={modules_history}
search=false
defaultSort={[{ id: 'timestamp', desc: true }]}>

    <Column id=timestamp title="Date" contentType=colorscale colorScale=info />
    <Column id=modules_converted title="With new Syntax" />
    <Column id=modules_with_old_pattern title="With old Syntax" />
    <Column id=modules_with_topics_version title="With Version Topics" />
    <Column id=modules_without_topics_version title="Without Version Topics" />
    <Column id=modules_with_wave_containers title="With Wave Containers" />
    <Column id=modules_without_wave_containers title="Without Wave Containers" />
    <Column id=total_modules title="Total" />

</DataTable>
