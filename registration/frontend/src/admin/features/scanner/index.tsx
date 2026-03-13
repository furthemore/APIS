/// <reference types="w3c-web-hid" />
import { HidPosDevice, SnapiDevice } from "@syfaro/scanners-and-such-web";
import { parse } from "date-fns/parse";
import { type MRTDDate } from "mrtd";

export { BarcodeScanner as default } from "./components/barcode-scanner";

export type DeviceDriverName = "snapi" | "usb-hid";
export type SupportedDevice = {
  name: DeviceDriverName;
  filters: HIDDeviceFilter[];
};

export type DeviceDriver = SnapiDevice | HidPosDevice;

export const HID_SUPPORTED = "hid" in navigator;

const SUPPORTED_DEVICES: SupportedDevice[] = [
  { name: "snapi", filters: [{ vendorId: 0x05e0, productId: 0x1900 }] },
  { name: "usb-hid", filters: [{ usagePage: 0x008c, usage: 0x0002 }] },
];

const ALL_FILTERS = SUPPORTED_DEVICES.flatMap(({ filters }) => filters);

const checkDeviceFilter = (
  device: HIDDevice,
  filter: HIDDeviceFilter,
): boolean => {
  if (filter.vendorId && device.vendorId !== filter.vendorId) return false;
  if (filter.productId && device.productId !== filter.productId) return false;
  if (
    filter.usagePage &&
    !device.collections.some(
      (collection) => collection.usagePage === filter.usagePage,
    )
  )
    return false;
  if (
    filter.usage &&
    !device.collections.some((collection) => collection.usage === filter.usage)
  )
    return false;

  return true;
};

export const filterDevices = (devices: HIDDevice[]): HIDDevice[] => {
  return devices.filter((device) =>
    ALL_FILTERS.some((filter) => checkDeviceFilter(device, filter)),
  );
};

export const driverNameForDevice = (
  device: HIDDevice,
): DeviceDriverName | undefined =>
  SUPPORTED_DEVICES.find((supported_device) =>
    supported_device.filters.some((filter) =>
      checkDeviceFilter(device, filter),
    ),
  )?.name;

export const requestHidDevice = async (): Promise<HIDDevice[]> => {
  return await navigator.hid.requestDevice({
    filters: ALL_FILTERS,
  });
};

export const mrtdDate = (d: MRTDDate, allowFuture: boolean): Date => {
  const [year, month, day] = [d.year, d.month, d.day].map((val) =>
    val.toString().padStart(2, "0"),
  );
  const currentDate = new Date();
  const val = parse(`${year}${month}${day}`, "yyMMdd", currentDate);
  if (val.getFullYear() > currentDate.getFullYear() - 20 && !allowFuture) {
    val.setFullYear(val.getFullYear() - 100);
  }
  return val;
};
