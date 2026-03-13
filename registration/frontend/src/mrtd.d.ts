declare module "mrtd" {
  declare type MRTD = {
    birthday: MRTDDate;
    documentNumber: string;
    documentSubType: string;
    documentType: string;
    expiry: MRTDDate;
    issuer: string;
    name: MRTDName;
    nationality: string;
    sex: string;
  };

  declare type MRTDName = {
    primary: string;
    secondary: string;
  };

  declare type MRTDDate = {
    year: string;
    month: string;
    day: string;
  };

  declare function parse(lines: string): MRTD;
}
