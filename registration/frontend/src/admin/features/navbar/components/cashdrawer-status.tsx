import { faRefresh } from "@fortawesome/free-solid-svg-icons";
import { Dialog } from "@kobalte/core/dialog";
import { createTimeAgo } from "@solid-primitives/date";
import { useQuery } from "@tanstack/solid-query";
import {
  type Accessor,
  type Component,
  Suspense,
  createEffect,
} from "solid-js";

import { cashStatusOptions } from "@admin/api";
import { cleanMoneyAmount } from "@admin/features/cart/utils";
import { Button } from "@components/button";
import { IconAndLabel } from "@components/icon-and-label";
import { Modal } from "@components/modal";

export const CashdrawerStatus: Component<{
  open: Accessor<boolean>;
  onOpenChange: (open: boolean) => void;
}> = (props) => {
  const status = useQuery(() => cashStatusOptions(props.open()));

  createEffect(() => {
    if (props.open()) {
      status.refetch();
    }
  });

  const [timeAgo] = createTimeAgo(() => status.dataUpdatedAt, {
    min: 5000,
    interval: 1000,
  });

  return (
    <Modal open={props.open} onOpenChange={props.onOpenChange}>
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <Dialog.Title as="h5" class="modal-title">
              Cashdrawer Status
            </Dialog.Title>

            <Dialog.CloseButton type="button" class="btn-close" />
          </div>

          <Dialog.Description as="div" class="modal-body">
            <Suspense fallback="Loading...">
              <div class="table-responsive">
                <table class="table">
                  <tbody>
                    <tr>
                      <th scope="row" style={{ width: "33%" }}>
                        Status
                      </th>
                      <td
                        classList={{
                          "table-success": status.data?.status === "OPEN",
                          "table-secondary": status.data?.status === "CLOSED",
                          "table-danger": status.data?.status === "SHORT",
                        }}
                      >
                        {status.data?.status}
                      </td>
                    </tr>
                    <tr>
                      <th scope="row">Total</th>
                      <td>
                        {status.data?.total &&
                          cleanMoneyAmount(status.data.total)}
                      </td>
                    </tr>
                    <tr>
                      <th scope="row">Last Updated</th>
                      <td>{timeAgo()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Suspense>
          </Dialog.Description>

          <div class="modal-footer">
            <Button
              type="button"
              class="btn btn-secondary"
              onClick={() => status.refetch()}
              loading={status.isFetching}
            >
              <IconAndLabel children="Refresh" icon={faRefresh} />
            </Button>

            <Dialog.CloseButton class="btn btn-primary">
              Close
            </Dialog.CloseButton>
          </div>
        </div>
      </div>
    </Modal>
  );
};
