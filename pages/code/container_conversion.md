---
title: Modules container conversion
sidebar_position: 9
---

# nf-core/modules linux_amd64 Usage

This page tracks the usage of the new con

```sql modules_latest
select
    timestamp,
    total_modules,
    modules_with_old_pattern,
    modules_converted,
    modules_with_topics_version,
    modules_without_topics_version,
    modules_with_wave_containers,
    modules_without_wave_containers,
    conversion_percentage
from nfcore_db.modules_container_conversion
order by timestamp desc
limit 1
```

```sql modules_over_time
select
    timestamp,
    modules_converted as "Modules with linux_amd64",
    modules_with_old_pattern as "Modules without linux_amd64"
from nfcore_db.modules_container_conversion
order by timestamp
```

```sql modules_over_time_pct
select
    timestamp,
    round(modules_converted * 100.0 / nullif(total_modules, 0), 2) as "Modules with linux_amd64",
    round(modules_with_old_pattern * 100.0 / nullif(total_modules, 0), 2) as "Modules without linux_amd64"
from nfcore_db.modules_container_conversion
order by timestamp
```

```sql topics_over_time
select
    timestamp,
    modules_with_topics_version as "Modules with topics: versions:",
    modules_without_topics_version as "Modules without topics: versions:"
from nfcore_db.modules_container_conversion
order by timestamp
```

```sql topics_over_time_pct
select
    timestamp,
    round(modules_with_topics_version * 100.0 / total_modules, 2) as "Modules with topics: versions:",
    round(modules_without_topics_version * 100.0 / total_modules, 2) as "Modules without topics: versions:"
from nfcore_db.modules_container_conversion
order by timestamp
```

```sql wave_over_time
select
    timestamp,
    modules_with_wave_containers as "Modules with Wave containers",
    modules_without_wave_containers as "Modules without Wave containers"
from nfcore_db.modules_container_conversion
order by timestamp
```

```sql wave_over_time_pct
select
    timestamp,
    round(modules_with_wave_containers * 100.0 / total_modules, 2) as "Modules with Wave containers",
    round(modules_without_wave_containers * 100.0 / total_modules, 2) as "Modules without Wave containers"
from nfcore_db.modules_container_conversion
order by timestamp
```

## Current Status

<BigValue
    data={modules_latest}
    value=conversion_percentage
    title="Usage Percentage"
    fmt=pct1
/>

<BigValue
    data={modules_latest}
    value=modules_converted
    title="Modules Using linux_amd64"
/>

<BigValue
    data={modules_latest}
    value=modules_with_old_pattern
    title="Modules Without linux_amd64"
/>

<BigValue
    data={modules_latest}
    value=total_modules
    title="Total Modules"
/>

<BigValue
    data={modules_latest}
    value=modules_with_topics_version
    title="Modules with topics: versions:"
/>

<BigValue
    data={modules_latest}
    value=modules_without_topics_version
    title="Modules without topics: versions:"
/>

<BigValue
    data={modules_latest}
    value=modules_with_wave_containers
    title="Modules with Wave containers"
/>

<BigValue
    data={modules_latest}
    value=modules_without_wave_containers
    title="Modules without Wave containers"
/>

## linux_amd64 Usage Over Time

<Tabs>
    <Tab label="Percentage" defaultTab>
        <AreaChart
            data={modules_over_time_pct}
            x=timestamp
            y={["Modules with linux_amd64", "Modules without linux_amd64"]}
            title="Module linux_amd64 Usage Timeline (%)"
            yAxisTitle="Percentage (%)"
        />
    </Tab>
    <Tab label="Total Numbers">
        <AreaChart
            data={modules_over_time}
            x=timestamp
            y={["Modules with linux_amd64", "Modules without linux_amd64"]}
            title="Module linux_amd64 Usage Timeline"
            yAxisTitle="Number of Modules"
        />
    </Tab>
</Tabs>

## topics: versions: Adoption Over Time

<Tabs>
    <Tab label="Percentage" defaultTab>
        <AreaChart
            data={topics_over_time_pct}
            x=timestamp
            y={["Modules with topics: versions:", "Modules without topics: versions:"]}
            title="topics: versions: Field Adoption Timeline (%)"
            yAxisTitle="Percentage (%)"
        />
    </Tab>
    <Tab label="Total Numbers">
        <AreaChart
            data={topics_over_time}
            x=timestamp
            y={["Modules with topics: versions:", "Modules without topics: versions:"]}
            title="topics: versions: Field Adoption Timeline"
            yAxisTitle="Number of Modules"
        />
    </Tab>
</Tabs>

## Wave Containers Adoption Over Time

<Tabs>
    <Tab label="Percentage" defaultTab>
        <AreaChart
            data={wave_over_time_pct}
            x=timestamp
            y={["Modules with Wave containers", "Modules without Wave containers"]}
            title="Wave Containers (community.wave.seqera.io) Adoption Timeline (%)"
            yAxisTitle="Percentage (%)"
        />
    </Tab>
    <Tab label="Total Numbers">
        <AreaChart
            data={wave_over_time}
            x=timestamp
            y={["Modules with Wave containers", "Modules without Wave containers"]}
            title="Wave Containers (community.wave.seqera.io) Adoption Timeline"
            yAxisTitle="Number of Modules"
        />
    </Tab>
</Tabs>

## Details

This page tracks three metrics for nf-core modules:

1. **linux_amd64 Usage**: How many modules specify `linux_amd64` architecture in their `meta.yml` files
2. **topics: versions: Field**: How many modules include the `topics:` section with `versions:` in their `meta.yml` files
3. **Wave Containers**: How many modules use `community.wave.seqera.io/library/` containers in their `main.nf` files

These metrics help understand metadata specification patterns and container adoption across the modules repository.

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
    conversion_percentage
from nfcore_db.modules_container_conversion
order by timestamp desc
```

<DataTable
    data={modules_history}
    search=false
    defaultSort={[{ id: 'timestamp', desc: true }]}
>
    <Column id=timestamp title="Date" contentType=colorscale scaleColor=blue />
    <Column id=conversion_percentage title="Usage %" fmt=pct1 contentType=colorscale scaleColor=green />
    <Column id=modules_converted title="With linux_amd64" />
    <Column id=modules_with_old_pattern title="Without linux_amd64" />
    <Column id=modules_with_topics_version title="With topics: versions:" />
    <Column id=modules_without_topics_version title="Without topics: versions:" />
    <Column id=modules_with_wave_containers title="With Wave containers" />
    <Column id=modules_without_wave_containers title="Without Wave containers" />
    <Column id=total_modules title="Total" />
</DataTable>
