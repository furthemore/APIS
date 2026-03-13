import type { Component } from "solid-js";

export const ErrorCard: Component<{
  title: string;
  err: any;
  reset: () => void;
}> = (props) => {
  return (
    <div class="card border-danger mb-3">
      <div class="card-header text-bg-danger">
        <div>{props.title}</div>
      </div>
      <div class="card-body">
        <p>{props.err.toString()}</p>

        <button
          type="button"
          class="btn btn-primary"
          onClick={() => props.reset()}
        >
          Reset
        </button>
      </div>
    </div>
  );
};
