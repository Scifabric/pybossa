create table bossa_app (
    id                  integer     not null auto_increment,
    create_time         integer     not null,
    name                varchar(255) not null,
    short_name          varchar(255) not null,
    description         varchar(255) not null,
    long_jobs           tinyint     not null,
    hidden              tinyint     not null,
    bolt_course_id      integer     not null,
    time_estimate       integer     not null,
    time_limit          integer     not null,
    calibration_frac    double      not null,
    info                text,
        -- app-specific info, JSON
    primary key(id)
) engine = InnoDB;

create table bossa_job (
    id                  integer     not null auto_increment,
    create_time         integer     not null,
    app_id              integer     not null,
    batch_id            integer     not null,
    state               integer     not null,
    info                text,
    calibration         tinyint     not null,
    priority_0          double      not null,
        -- add more as needed
        -- for calibration jobs, init to random and decrement on each view
    primary key(id)
) engine=InnoDB;

create table bossa_job_inst (
    id                  integer     not null auto_increment,
    create_time         integer     not null,
    app_id              integer     not null,
    job_id              integer     not null,
    user_id             integer     not null,
    batch_id            integer     not null,
    finish_time         integer     not null,
    timeout             integer     not null,
    calibration         tinyint     not null,
    info                text,
    primary key(id)
) engine=InnoDB;

create table user (
    id                      integer         not null auto_increment,                                                                                                     
    create_time             integer         not null,
    email_addr              varchar(254)    not null,
    name                    varchar(254),
    authenticator           varchar(254),
    country                 varchar(254),
    postal_code             varchar(254),
    total_credit            double          not null,
    expavg_credit           double          not null,
    expavg_time             double          not null,
    global_prefs            blob,
    project_prefs           blob,
    teamid                  integer         not null,
    venue                   varchar(254)    not null,
    url                     varchar(254),
    send_email              smallint        not null,
    show_hosts              smallint        not null,
    posts                   smallint        not null,
        -- reused: salt for weak auth
    seti_id                 integer         not null,
    seti_nresults           integer         not null,
    seti_last_result_time   integer     not null,
    seti_total_cpu          double          not null,
    signature               varchar(254),
        -- deprecated
    has_profile             smallint        not null,
    cross_project_id        varchar(254)    not null,
    passwd_hash             varchar(254)    not null,
    email_validated         smallint        not null,
    donated                 smallint        not null,
    primary key (id)
) engine=InnoDB;

create table bossa_user (
    user_id             integer     not null,
    category            integer     not null,
    flags               integer     not null,
        -- debug, show_all
    info                text,
        -- Project-dependent info about users ability and performance.
    primary key(user_id)
) engine = InnoDB;

create table bossa_batch (
    id                  integer     not null auto_increment,
    create_time         integer     not null,
    name                varchar(255) not null,
    app_id              integer     not null,
    calibration         tinyint     not null,
    primary key(id)
) engine = InnoDB;
