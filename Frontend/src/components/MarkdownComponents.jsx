import React from 'react';

export const ModernTable = (props) => (
    <div className="table-container">
        <table className="glass-table" {...props} />
    </div>
);

export const ModernThead = (props) => (
    <thead className="glass-thead" {...props} />
);

export const ModernTbody = (props) => (
    <tbody className="glass-tbody" {...props} />
);

export const ModernTr = (props) => (
    <tr className="glass-tr" {...props} />
);

export const ModernTh = (props) => (
    <th className="glass-th" {...props} />
);

export const ModernTd = (props) => (
    <td className="glass-td" {...props} />
);
