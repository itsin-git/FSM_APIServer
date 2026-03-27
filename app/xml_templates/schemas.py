"""
XML payload templates for FortiSIEM event/query APIs.
Mirrors the schemas used in the FortiSOAR connector.
"""

INCIDENT_SCHEMA = """\
<?xml version="1.0" encoding="UTF-8"?>
<Reports>
   <Report baseline="" rsSync="">
      <PatternClause>
         <SubPattern id="" name="">
            <SingleEvtConstr>(phEventCategory = 1) AND (phCustId IN (1))</SingleEvtConstr>
         </SubPattern>
      </PatternClause>
      <SelectClause>
         <AttrList>{select_clause}</AttrList>
      </SelectClause>
      <OrderByClause>
         <AttrList>phRecvTime DESC</AttrList>
      </OrderByClause>
      <SyncOrgs/>
      <ReportInterval>{time_duration}</ReportInterval>
   </Report>
</Reports>"""

REPORT_SCHEMA = """\
<Reports><Report group="report">
     <Name></Name>
     <Description></Description>
     <CustomerScope groupByEachCustomer="false">
          <Include all="true"/>
          <Exclude/>
     </CustomerScope>
     <SelectClause>
          <AttrList>{attr_list}</AttrList>
     </SelectClause>
     <OrderByClause>
          <AttrList>{orderby}</AttrList>
     </OrderByClause>
     <ReportInterval>
         {time_duration}
     </ReportInterval>
     <PatternClause>
          <SubPattern id="Reports" name="Reports">
               <SingleEvtConstr>{conditions}</SingleEvtConstr>
               <GroupByAttr>{groupby}</GroupByAttr>
          </SubPattern>
     </PatternClause>
     <SyncOrgs/>
    </Report>
</Reports>"""

SQL_QUERY_SCHEMA = """\
<?xml version="1.0" encoding="UTF-8"?>
<Reports>
    <Report>
        <Name>SQL Query</Name>
        <PatternClause/>
        <ClickHouseSQL>
            <SQL>
                <![CDATA[{sql_query}]]>
            </SQL>
            <CTES/>
        </ClickHouseSQL>
    </Report>
</Reports>"""

SCHEMA_BY_EVENT_ID = """\
<?xml version="1.0" encoding="UTF-8"?>
<Reports>
    <Report baseline="" rsSync="">
        <PatternClause>
            <SubPattern id="" name="">
                <SingleEvtConstr>{event_id_filter}</SingleEvtConstr>
            </SubPattern>
        </PatternClause>
        <SelectClause>
            <AttrList>{select_clause}</AttrList>
        </SelectClause>
        <OrderByClause>
            <AttrList>phRecvTime DESC</AttrList>
        </OrderByClause>
        <SyncOrgs/>
        <ReportInterval>{time_duration}</ReportInterval>
    </Report>
</Reports>"""

SEARCH_EVENT_SCHEMA = """\
<?xml version="1.0" encoding="UTF-8"?>
<Reports>
    <Report baseline="" id="" rsSync="">
        <Name>{report_name}</Name>
        <Description></Description>
        <CustomerScope groupByEachCustomer="false">
            <Include all="true"/>
            <Exclude/>
        </CustomerScope>
        <PatternClause>
            <SubPattern id="" name="">
                <SingleEvtConstr>{query_string}</SingleEvtConstr>
            </SubPattern>
        </PatternClause>
        <SelectClause>
            <AttrList>{select_clause}</AttrList>
        </SelectClause>
        <OrderByClause>
            <AttrList>phRecvTime DESC</AttrList>
        </OrderByClause>
        <ReportInterval>
            {time_duration}
        </ReportInterval>
    </Report>
</Reports>"""

DISCOVER_DEVICE_SCHEMA = """\
<discoverRequest>
    <type>{disc_type}</type>
    <includeRange>{include_ip}</includeRange>
    <excludeRange>{exclude_ip}</excludeRange>
    <noPing>{noping}</noPing>
    <onlyPing>{onlyping}</onlyPing>
</discoverRequest>"""
